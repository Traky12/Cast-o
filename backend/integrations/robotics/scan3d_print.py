"""
Scan-to-Print (laboratorio TRL-4): sin malla real ni slicer embebido; métricas simuladas + sellado Dilithium.
El GCode físico sale de Bambu Studio / PrusaSlicer / Cura en estación de trabajo, no de este stub.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import time
from typing import Any, Callable, Dict, List, Optional

import numpy as np
from fastapi import APIRouter, Depends, FastAPI, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field

from backend.integrations.robotics.neuromorphic_edge import HydroponicsSNN
from backend.security.pq_crypto import PostQuantumCrypto

logger = logging.getLogger(__name__)


def _max_build_mm() -> float:
    return float(os.getenv("CASTUO_PRINT_MAX_BUILD_MM", "256").strip() or "256")


def _dilithium_seal(payload: Dict[str, Any]) -> str:
    pqc = PostQuantumCrypto()
    msg = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return pqc.dilithium_sign(msg)


class ScanSimulateRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    filename: str = Field(default="lab_scan.ply", max_length=256)
    points: int = Field(default=10_000, ge=100, le=200_000)
    format: str = Field(default="pointcloud", max_length=64)


class Scan3DResult(BaseModel):
    mesh_points: int
    volume_cm3: float
    bbox_mm: List[float]
    material_recommended: str
    trl: str = "TRL-4-lab-sim"


class Scan3DLabResponse(BaseModel):
    result: Scan3DResult
    chain_seal: str


class PrintJobIn(BaseModel):
    model_config = ConfigDict(extra="ignore")

    scan_id: str = Field(..., min_length=1, max_length=128)
    printer_model: str = Field(default="generic_fdm", max_length=128)
    infill: int = Field(default=20, ge=0, le=100)
    layer_height: float = Field(default=0.2, gt=0, le=1.0)
    material: str = Field(default="PLA+", max_length=64)
    nozzle_temp: int = Field(default=220, ge=150, le=320)
    volume_cm3: Optional[float] = Field(default=None, ge=0, le=10_000)
    apply_neuro_hints: bool = Field(
        default=False,
        description="Si true, añade sugerencias neuromórficas (volumen) sin sobrescribir el job.",
    )
    chain_token_id: Optional[int] = Field(
        default=None,
        ge=0,
        description="tokenId para register_event_in_chain; si null, usa CASTUO_ROBOTICS_LAB_CHAIN_TOKEN_ID.",
    )


class PrintLabResponse(BaseModel):
    status: str = "gcode-ready"
    print_job: Dict[str, Any]
    chain_seal: str
    neuro_hints: Optional[Dict[str, Any]] = None
    on_chain_tx_hash: Optional[str] = None
    chain_registration: str = "none"


def _simulate_from_point_count(filename: str, points: int) -> Scan3DResult:
    seed = int(hashlib.sha256(filename.encode("utf-8")).hexdigest()[:8], 16)
    rng = np.random.default_rng(seed)
    k = min(5000, max(200, points // 20))
    sample = rng.normal(0, 10, size=(k, 3))
    max_mm = _max_build_mm()
    ranges = [float(np.ptp(sample[:, i])) for i in range(3)]
    bbox = [min(max_mm, max(1.0, r)) for r in ranges]
    vol = float(np.clip(5.0 + (points % 50_000) / 400.0 + rng.uniform(0, 25), 5.0, 150.0))
    mat = "PLA+" if vol < 50 else "PETG"
    return Scan3DResult(
        mesh_points=int(points),
        volume_cm3=round(vol, 3),
        bbox_mm=bbox,
        material_recommended=mat,
    )


def attach_scan3d_routes(app: FastAPI, auth_dep: Callable[..., Any]) -> None:
    router = APIRouter(prefix="/api/robotics/lab/scan3d", tags=["scan3d-lab"])

    @router.post("/scan", response_model=Scan3DLabResponse)
    async def scan_lab_json(
        body: ScanSimulateRequest,
        _: None = Depends(auth_dep),
    ) -> Scan3DLabResponse:
        result = _simulate_from_point_count(body.filename, body.points)
        audit = {
            "kind": "scan3d_lab",
            "result": result.model_dump(),
            "source_filename": body.filename,
            "format": body.format,
            "ts_unix": time.time(),
        }
        return Scan3DLabResponse(result=result, chain_seal=_dilithium_seal(audit))

    @router.post("/scan/upload", response_model=Scan3DLabResponse)
    async def scan_lab_upload(
        request: Request,
        _: None = Depends(auth_dep),
    ) -> Scan3DLabResponse:
        raw = await request.body()
        if len(raw) > 50 * 1024 * 1024:
            raise HTTPException(status_code=413, detail="Archivo demasiado grande para el lab (máx 50MB).")
        n = int(min(200_000, max(1_000, len(raw) // 3 + 5_000)))
        cd = request.headers.get("content-disposition", "")
        fname = "upload.bin"
        if "filename=" in cd:
            fname = cd.split("filename=", 1)[-1].strip().strip('"')[:256] or fname
        result = _simulate_from_point_count(fname, n)
        audit = {
            "kind": "scan3d_upload_lab",
            "result": result.model_dump(),
            "upload_bytes": len(raw),
            "filename": fname,
            "ts_unix": time.time(),
        }
        return Scan3DLabResponse(result=result, chain_seal=_dilithium_seal(audit))

    @router.post("/print", response_model=PrintLabResponse)
    async def slice_print_lab(
        job: PrintJobIn,
        _: None = Depends(auth_dep),
    ) -> PrintLabResponse:
        volume = job.volume_cm3
        if volume is None:
            volume = 30.0
        gcode_size_mb = min(25.0, (job.infill / 100.0) * 25.0)
        print_time_h = round(float(volume) * 0.1, 3)
        gcode_meta = {
            "file_size_mb": round(gcode_size_mb, 3),
            "print_time_h": print_time_h,
            "gcode_commands": 15_000,
            "material_usage_g": int(volume * 1.25),
            "layer_height_mm": job.layer_height,
            "material": job.material,
            "nozzle_temp_c": job.nozzle_temp,
        }
        audit = {"kind": "print_job_lab", "scan_id": job.scan_id, "summary": gcode_meta, "ts_unix": time.time()}
        seal = _dilithium_seal(audit)
        neuro_hints = None
        if job.apply_neuro_hints:
            neuro_hints = HydroponicsSNN().optimize_print_params_from_volume(float(volume))
        on_tx = None
        chain_registration = "none"
        from backend.integrations.robotics.lab_gaiachain_optional import (
            build_scan3d_print_audit_payload,
            resolve_snapshot_token_id,
            robotics_lab_chain_register_enabled,
            try_register_lab_audit_event,
        )

        tid = (
            int(job.chain_token_id)
            if job.chain_token_id is not None and job.chain_token_id > 0
            else resolve_snapshot_token_id(None)
        )
        if robotics_lab_chain_register_enabled() and tid > 0:
            payload = build_scan3d_print_audit_payload(
                token_id=tid,
                scan_id=job.scan_id,
                chain_seal_dilithium=seal,
                volume_cm3=float(volume),
                material=job.material,
            )
            on_tx = try_register_lab_audit_event(payload)
            chain_registration = "registered" if on_tx else "failed"
        elif robotics_lab_chain_register_enabled() and tid <= 0:
            chain_registration = "missing_token"

        return PrintLabResponse(
            print_job=gcode_meta,
            chain_seal=seal,
            neuro_hints=neuro_hints,
            on_chain_tx_hash=on_tx,
            chain_registration=chain_registration,
        )

    app.include_router(router)
