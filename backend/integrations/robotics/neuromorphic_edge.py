"""
Simulador TRL-4: SNN ligera + sinapsis tipo memristor (sin hardware Loihi2/NeuRRAM en este repo).
Sellado: Dilithium vía PostQuantumCrypto (o ruta simulada documentada en pq_crypto).
"""

from __future__ import annotations

import hashlib
import json
import logging
import math
import os
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional

import numpy as np
from fastapi import APIRouter, Depends, FastAPI
from pydantic import BaseModel, ConfigDict, Field

from backend.security.pq_crypto import PostQuantumCrypto

logger = logging.getLogger(__name__)


def _canonical_sensors_json(sensors: Dict[str, float]) -> str:
    norm = {k: float(sensors[k]) for k in sorted(sensors)}
    return json.dumps(norm, sort_keys=True, separators=(",", ":"))


def snn_cache_key(sensors: Dict[str, float]) -> str:
    h = hashlib.sha256(_canonical_sensors_json(sensors).encode("utf-8")).hexdigest()
    return f"castuo:snn:v1:{h}"


def _sensors_seed(sensors: Dict[str, float]) -> int:
    digest = hashlib.sha256(_canonical_sensors_json(sensors).encode("utf-8")).hexdigest()
    return int(digest[:12], 16) % (2**31)


def _jsonable_for_cache(obj: Any) -> Any:
    if obj is None or isinstance(obj, (str, int, float, bool)):
        return obj
    if isinstance(obj, dict):
        return {k: _jsonable_for_cache(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_jsonable_for_cache(x) for x in obj]
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if hasattr(obj, "item"):
        try:
            return obj.item()
        except Exception:
            return float(obj)
    return str(obj)


def redis_client_snn_cache() -> Any:
    url = (os.getenv("CASTUO_SNN_CACHE_REDIS_URL") or "").strip()
    if not url:
        return None
    try:
        import redis  # type: ignore

        return redis.Redis.from_url(
            url,
            decode_responses=True,
            socket_connect_timeout=2.0,
            socket_timeout=2.0,
        )
    except Exception as exc:
        logger.warning("Redis caché SNN no disponible (se ignora): %s", exc)
        return None


def snn_cache_ttl_seconds() -> int:
    """
    TTL Redis para entradas SNN: prioridad CASTUO_SNN_CACHE_TTL_SECONDS (entero ≥30);
    si no, mapa CASTUO_SNN_CACHE_SEASON (verano|invierno|primavera|otoño); default 300.
    Política de estación = orientativa; ajustar según agronomía y hit-rate medido.
    """
    explicit = (os.getenv("CASTUO_SNN_CACHE_TTL_SECONDS") or "").strip()
    if explicit:
        try:
            return max(30, int(explicit))
        except ValueError:
            logger.debug("CASTUO_SNN_CACHE_TTL_SECONDS inválido, se usa estación o default")
    season = (os.getenv("CASTUO_SNN_CACHE_SEASON") or "").strip().lower()
    seasonal = {"verano": 600, "invierno": 300, "primavera": 450, "otoño": 450}
    if season in seasonal:
        return seasonal[season]
    return 300


def _eco_alloy_label() -> str:
    return (os.getenv("CASTUO_ECO_ALLOY", "Cs2AgBiBr6").strip() or "Cs2AgBiBr6")


@dataclass
class MemristorSynapse:
    conductance: float = 0.5
    weight: float = 0.0
    eco_alloy: str = field(default_factory=_eco_alloy_label)

    def update_stdp(self, pre_spike: bool, post_spike: bool, dt: float) -> float:
        dt = abs(float(dt))
        if pre_spike and post_spike:
            self.weight += 0.01 * math.exp(-dt / 10.0)
        elif post_spike and not pre_spike:
            self.weight -= 0.01 * math.exp(-dt / 10.0)
        self.conductance = max(0.01, abs(self.weight))
        return self.weight


class HydroponicsSNN:
    def __init__(self, neurons: int = 128) -> None:
        self.synapses: List[MemristorSynapse] = [MemristorSynapse() for _ in range(neurons)]
        self.spike_threshold: float = 1.0
        self.potentials: np.ndarray = np.zeros(neurons, dtype=np.float64)

    def process_sensors(
        self,
        inputs: Dict[str, float],
        rng: Optional[np.random.Generator] = None,
    ) -> Dict[str, Any]:
        humedad = float(inputs.get("humedad", 0.0))
        ph = float(inputs.get("ph", 7.0))
        ec = float(inputs.get("ec", 0.0))
        luz = float(inputs.get("luz_umol", inputs.get("luz", 0.0)))
        lam = max(0.05, min(5.0, humedad / 100.0 + ec * 0.1 + abs(7.0 - ph) * 0.02))
        if rng is None:
            spikes = np.random.poisson(lam, size=len(self.synapses))
        else:
            spikes = rng.poisson(lam, size=len(self.synapses))

        for i, (syn, spike) in enumerate(zip(self.synapses, spikes)):
            if spike > 0:
                self.potentials[i] += syn.conductance * 0.1
                if self.potentials[i] > self.spike_threshold:
                    self.potentials[i] = 0.0
                    syn.update_stdp(pre_spike=True, post_spike=True, dt=5.0)

        mean_g = float(np.mean([s.conductance for s in self.synapses])) if self.synapses else 0.0
        riego_ml = int(np.clip(np.sum(self.potentials) * 10.0 + humedad * 5.0 + ec * 20.0, 0.0, 1000.0))
        return {
            "riego_ml": riego_ml,
            "memristor_power_uW": mean_g * 1e-6,
            "alloy_integrity": 0.98,
            "eco_alloy": _eco_alloy_label(),
            "trl": "TRL-4-lab-sim",
            "inputs_echo": {"humedad": humedad, "ph": ph, "ec": ec, "luz_umol": luz},
        }

    def optimize_print_params_from_volume(self, volume_cm3: float) -> Dict[str, Any]:
        """Heurística TRL-4 para acoplar impresión FDM a volumen estimado (no sustituye slicer)."""
        v = float(volume_cm3)
        if v < 20.0:
            return {"infill": 15, "speed": "high", "note": "prototipo_rapido_lab"}
        return {"infill": 30, "speed": "precision", "note": "carga_estructural_lab"}


def _hydro_traceability_block(target_terpene: Optional[str]) -> Dict[str, Any]:
    """Metadatos de auditoría ética/legal; no forman parte del payload firmado SNN base."""
    try:
        from agrotech.terpene_profiles import ETHICS_NOTICE_SHORT, TERPENE_PROFILES_VERSION

        ver = TERPENE_PROFILES_VERSION
        notice = ETHICS_NOTICE_SHORT
    except ImportError:
        ver = "unknown"
        notice = "Trazabilidad agrotech: módulo agrotech no importable en este despliegue."
    tt = (target_terpene or "").strip().lower() or None
    paths = [
        "agrotech/ETHICS_TRACEABILITY.md",
        "deploy/CHECKLIST-TRL7-INDUSTRIAL-LIVE.md",
        "docs/legal/MARCO-LEGAL-SOBERANIA-UE-2026.md",
    ]
    base = (os.getenv("CASTUO_GOVERNANCE_DOCS_BASE_URL") or "").strip().rstrip("/")
    urls = [f"{base}/{p}" for p in paths] if base else []
    trl_env = (os.getenv("TRL_LEVEL") or "TRL-6-staging").strip()
    trl_u = trl_env.upper()
    trl6_active = "TRL-6" in trl_u
    purpose = "agronomic_research_TRL6" if trl6_active else "agronomic_research"
    validation_checks = [
        "input_validation",
        "profile_compliance",
        "system_integrity",
    ]
    integration_gate = "TRL-6-staging" if trl6_active else "not-applicable"
    model_tier = "TRL-6-staging" if trl6_active else "research_grade"
    return {
        "profiles_version": ver,
        "terpene_profiles_version": ver,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "processing_purpose": purpose,
        "no_medical_advice": True,
        "no_regulatory_compliance_claim": True,
        "ethics_notice_short": notice,
        "governance_doc_paths": paths,
        "governance_doc_urls": urls,
        "target_terpene_requested": tt,
        "trl": trl_env,
        "model_tier": model_tier,
        "model_implementation_note": "SNN TRL-4 (NeuromorphicEdge v2.0)",
        "validation_checks": validation_checks,
        "tier_disclosure": {
            "neuromorphic_simulation": "TRL-4-lab-sim",
            "integration_gate": integration_gate,
        },
    }


def seal_inference_payload(payload: Dict[str, Any]) -> str:
    pqc = PostQuantumCrypto()
    msg = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return pqc.dilithium_sign(msg)


def hydro_infer_dict(sensors: Dict[str, float]) -> Dict[str, Any]:
    r = redis_client_snn_cache()
    key = snn_cache_key(sensors) if r else None
    if r and key:
        try:
            raw = r.get(key)
            if raw:
                return json.loads(raw)
        except Exception as exc:
            logger.debug("snn cache get: %s", exc)

    if r:
        rng = np.random.default_rng(_sensors_seed(sensors))
    else:
        rng = None
    snn = HydroponicsSNN()
    decision = snn.process_sensors(sensors, rng=rng)
    seal = seal_inference_payload({"sensors": sensors, "decision": decision})
    out: Dict[str, Any] = {"inference": decision, "chain_seal": seal}
    if r and key:
        try:
            ttl = snn_cache_ttl_seconds()
            payload = json.dumps(_jsonable_for_cache(out), sort_keys=True, separators=(",", ":"))
            r.setex(key, ttl, payload)
        except Exception as exc:
            logger.debug("snn cache set: %s", exc)
    return out


def neuromorphic_hint_from_metadata(metadata: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    if os.getenv("CASTUO_NEUROMORPHIC_LAB", "").strip() != "1":
        return None
    keys = ("humedad", "ph", "ec", "luz_umol", "luz")
    if not any(k in metadata for k in keys):
        return None
    sensors: Dict[str, float] = {}
    if "humedad" in metadata:
        sensors["humedad"] = float(metadata["humedad"])
    if "ph" in metadata:
        sensors["ph"] = float(metadata["ph"])
    if "ec" in metadata:
        sensors["ec"] = float(metadata["ec"])
    if "luz_umol" in metadata:
        sensors["luz_umol"] = float(metadata["luz_umol"])
    elif "luz" in metadata:
        sensors["luz"] = float(metadata["luz"])
    try:
        return hydro_infer_dict(sensors)
    except Exception as exc:
        logger.warning("neuromorphic_hint_from_metadata: %s", exc)
        return None


class HydroSensorIn(BaseModel):
    model_config = ConfigDict(extra="ignore")

    humedad: float = Field(default=0.0, ge=0.0, le=100.0)
    ph: float = Field(default=7.0, ge=0.0, le=14.0)
    ec: float = Field(default=0.0, ge=0.0, le=50.0)
    luz_umol: float = Field(default=0.0, ge=0.0, le=3000.0)
    uvb_ratio: float = Field(default=0.0, ge=0.0, le=1.0)
    target_terpene: Optional[str] = Field(default=None, min_length=1, max_length=64)


class HydroInferResponse(BaseModel):
    riego_ml: int
    power_uW: float
    chain_seal: str
    eco_alloy: str
    inference: Dict[str, Any]


def attach_neuromorphic_routes(app: FastAPI, auth_dep: Callable[..., Any]) -> None:
    router = APIRouter(prefix="/api/robotics/lab/neuromorphic", tags=["neuromorphic-lab"])

    @router.post("/hydroponics/infer", response_model=HydroInferResponse)
    async def neuro_infer(
        sensors: HydroSensorIn,
        _: None = Depends(auth_dep),
    ) -> HydroInferResponse:
        t0 = time.perf_counter()
        body = sensors.model_dump(exclude_none=True)
        target_terpene = body.pop("target_terpene", None)
        uvb_ratio = float(body.pop("uvb_ratio", 0.0))
        sens = {k: float(v) for k, v in body.items()}
        out = hydro_infer_dict(sens)
        if uvb_ratio:
            out.setdefault("inference", {})["uvb_ratio"] = uvb_ratio
        if target_terpene:
            # Conserva el objetivo terpénico para trazabilidad n8n/lab sin alterar el cálculo SNN.
            out.setdefault("inference", {})["target_terpene"] = str(target_terpene).strip().lower()
        out.setdefault("inference", {})["traceability"] = _hydro_traceability_block(
            str(target_terpene) if target_terpene else None
        )
        try:
            from backend.integrations.robotics.lab_metrics_optional import record_neuro_infer_seconds

            record_neuro_infer_seconds(time.perf_counter() - t0, int(out["inference"]["riego_ml"]))
        except Exception:
            pass
        dec = out["inference"]
        return HydroInferResponse(
            riego_ml=int(dec["riego_ml"]),
            power_uW=float(dec["memristor_power_uW"]),
            chain_seal=out["chain_seal"],
            eco_alloy=str(dec.get("eco_alloy", _eco_alloy_label())),
            inference=dec,
        )

    app.include_router(router)
