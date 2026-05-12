#!/usr/bin/env python3
"""Satellite STAC ingestion worker (EU sovereign profile).

This worker pulls metadata from configured satellite/public APIs and emits a
normalized catalog record that can be stored as STAC-like JSON.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

import httpx


COPERNICUS_STAC_URL = os.getenv(
    "COPERNICUS_STAC_URL",
    "https://catalogue.dataspace.copernicus.eu/stac",
)
EUMETSAT_API_URL = os.getenv("EUMETSAT_API_URL", "https://api.eumetsat.int")
SIGPAC_API_URL = os.getenv("SIGPAC_API_URL", "https://sigpac.mapa.gob.es/api")
SIEX_API_URL = os.getenv("SIEX_API_URL", "https://siex.mapa.gob.es/api")
OUTPUT_DIR = Path(os.getenv("SATELLITE_CATALOG_OUTPUT", "/data/satellite/catalog"))


def _safe_get(client: httpx.Client, url: str) -> dict:
    try:
        response = client.get(url, timeout=15.0)
        response.raise_for_status()
        if "application/json" in response.headers.get("content-type", ""):
            return response.json()
        return {"status": "ok", "note": "non-json response"}
    except Exception as exc:  # pragma: no cover - network dependent
        return {"status": "error", "error": str(exc), "url": url}


def run_once() -> Path:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with httpx.Client() as client:
        record = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "sources": {
                "copernicus": _safe_get(client, COPERNICUS_STAC_URL),
                "eumetsat": _safe_get(client, EUMETSAT_API_URL),
                "sigpac": _safe_get(client, SIGPAC_API_URL),
                "siex": _safe_get(client, SIEX_API_URL),
            },
            "sovereignty": {
                "region": "EU",
                "policy": "GDPR-minimization",
            },
        }

    out_file = OUTPUT_DIR / f"stac-catalog-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.json"
    out_file.write_text(json.dumps(record, ensure_ascii=True, indent=2), encoding="utf-8")
    return out_file


if __name__ == "__main__":
    saved = run_once()
    print(f"[OK] Catalog saved: {saved}")
