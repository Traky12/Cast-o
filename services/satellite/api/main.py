from __future__ import annotations

import json
import os
from pathlib import Path

import numpy as np
import rasterio
from fastapi import FastAPI, HTTPException


app = FastAPI(title="CASTUO Satellite NDVI API", version="0.1.0")
NDVI_BASE_DIR = Path(os.getenv("NDVI_DATA_DIR", "/data/ndvi"))
NDMI_BASE_DIR = Path(os.getenv("NDMI_DATA_DIR", "/data/ndmi"))
EVIDENCE_INDEX_PATH = Path(os.getenv("EVIDENCE_INDEX_PATH", "/data/evidence/index.json"))


@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "service": "ndvi-api"}


@app.get("/ndvi/{image_id}")
async def get_ndvi_stats(image_id: str) -> dict:
    target = NDVI_BASE_DIR / f"{image_id}.tif"
    if not target.exists():
        raise HTTPException(status_code=404, detail=f"NDVI file not found: {target.name}")

    with rasterio.open(target) as src:
        ndvi = src.read(1)
        stats = {
            "image_id": image_id,
            "min": float(np.nanmin(ndvi)),
            "max": float(np.nanmax(ndvi)),
            "mean": float(np.nanmean(ndvi)),
        }
    return stats


@app.get("/ndmi/{image_id}")
async def get_ndmi_stats(image_id: str) -> dict:
    target = NDMI_BASE_DIR / f"{image_id}.tif"
    if not target.exists():
        raise HTTPException(status_code=404, detail=f"NDMI file not found: {target.name}")

    with rasterio.open(target) as src:
        ndmi = src.read(1)
        stats = {
            "image_id": image_id,
            "min": float(np.nanmin(ndmi)),
            "max": float(np.nanmax(ndmi)),
            "mean": float(np.nanmean(ndmi)),
        }
    return stats


@app.get("/evidence/{asset_id}")
async def get_asset_evidence(asset_id: str) -> dict:
    if not EVIDENCE_INDEX_PATH.exists():
        raise HTTPException(status_code=404, detail="Evidence index not found")

    with EVIDENCE_INDEX_PATH.open("r", encoding="utf-8") as fh:
        data = json.load(fh)

    record = data.get(asset_id)
    if not record:
        raise HTTPException(status_code=404, detail=f"Evidence not found for asset: {asset_id}")
    return {"asset_id": asset_id, "evidence": record}
