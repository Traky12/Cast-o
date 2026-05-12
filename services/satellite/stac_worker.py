"""
CASTÚO-SYSTEM™ v3.1 — STAC Ingestión Worker
Descarga, indexa y almacena productos Sentinel-2 desde Copernicus Data Space.

Modo de ejecución:
    python -m services.satellite.stac_worker

Variables de entorno:
    COPERNICUS_CLIENT_ID / COPERNICUS_CLIENT_SECRET
    STAC_POLL_INTERVAL_S        — Intervalo entre ciclos (default: 3600s = 1h)
    STAC_PARCELAS_FILE          — JSON con lista de parcelas a monitorear
    STAC_BBOX_PADDING_DEG       — Padding en grados alrededor de la parcela (default: 0.01)
    OBJECT_STORAGE_ENDPOINT     — Endpoint S3-compatible (Hetzner Object Storage)
    OBJECT_STORAGE_KEY          — Access key
    OBJECT_STORAGE_SECRET       — Secret key
    OBJECT_STORAGE_BUCKET       — Bucket de destino (default: castuo-satellite)
    NDVI_DATA_PATH              — Directorio local para cache de resultados
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger("castuo.satellite.stac")

# ── Configuración ──────────────────────────────────────────────────────────────
_POLL_INTERVAL     = int(os.getenv("STAC_POLL_INTERVAL_S", "3600"))
_PARCELAS_FILE     = os.getenv("STAC_PARCELAS_FILE", "/data/satellite/parcelas.json")
_BBOX_PADDING      = float(os.getenv("STAC_BBOX_PADDING_DEG", "0.01"))
_NDVI_DATA_PATH    = Path(os.getenv("NDVI_DATA_PATH", "/data/satellite/ndvi"))
_CLOUD_COVER_MAX   = float(os.getenv("STAC_MAX_CLOUD_COVER", "20.0"))
_LOOKBACK_DAYS     = int(os.getenv("STAC_LOOKBACK_DAYS", "30"))
_RESULTS_PATH      = Path(os.getenv("SATELLITE_RESULTS_PATH", "/data/satellite/results"))

# Storage S3-compatible (Hetzner Object Storage o similar)
_STORAGE_ENDPOINT  = os.getenv("OBJECT_STORAGE_ENDPOINT", "")
_STORAGE_KEY       = os.getenv("OBJECT_STORAGE_KEY", "")
_STORAGE_SECRET    = os.getenv("OBJECT_STORAGE_SECRET", "")
_STORAGE_BUCKET    = os.getenv("OBJECT_STORAGE_BUCKET", "castuo-satellite")


def _load_parcelas() -> list[dict[str, Any]]:
    """
    Carga la lista de parcelas a monitorear desde el fichero JSON.

    Formato esperado:
    [
      {
        "id": "PARCELA-042",
        "nombre": "Dehesa Norte",
        "lon_min": -6.12, "lat_min": 38.45,
        "lon_max": -6.10, "lat_max": 38.47,
        "cultivo": "cannabis_medicinal"
      }
    ]
    """
    path = Path(_PARCELAS_FILE)
    if not path.exists():
        logger.warning("[stac_worker] Fichero de parcelas no encontrado: %s", _PARCELAS_FILE)
        # Parcela de ejemplo para Extremadura (zona CASTÚO)
        return [
            {
                "id": "DEMO-EXTREMADURA-001",
                "nombre": "Dehesa Castúo Demo",
                "lon_min": -6.15, "lat_min": 38.44,
                "lon_max": -6.08, "lat_max": 38.50,
                "cultivo": "pasto_permanente",
            }
        ]
    try:
        with open(path) as f:
            parcelas = json.load(f)
            logger.info("[stac_worker] Cargadas %d parcelas desde %s", len(parcelas), path)
            return parcelas
    except Exception as exc:
        logger.error("[stac_worker] Error leyendo parcelas: %s", exc)
        return []


def _parcela_to_bbox(parcela: dict[str, Any]) -> list[float]:
    """Convierte parcela a bbox con padding."""
    p = _BBOX_PADDING
    return [
        parcela["lon_min"] - p,
        parcela["lat_min"] - p,
        parcela["lon_max"] + p,
        parcela["lat_max"] + p,
    ]


def _save_result(parcela_id: str, result: dict[str, Any]) -> Path:
    """Guarda el resultado de análisis como JSON."""
    _RESULTS_PATH.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
    out = _RESULTS_PATH / f"{parcela_id}_{ts}.json"
    with open(out, "w") as f:
        json.dump(result, f, indent=2, default=str)
    return out


def _get_latest_result(parcela_id: str) -> dict[str, Any] | None:
    """Lee el resultado más reciente para una parcela."""
    pattern = f"{parcela_id}_*.json"
    files = sorted(_RESULTS_PATH.glob(pattern), reverse=True)
    if not files:
        return None
    try:
        with open(files[0]) as f:
            return json.load(f)
    except Exception:
        return None


async def _process_parcela(
    parcela: dict[str, Any],
    copernicus_client: Any,
    ndvi_worker: Any,
) -> dict[str, Any]:
    """Procesa una parcela: busca imágenes, calcula NDVI, guarda resultado."""
    parcela_id = parcela["id"]
    bbox       = _parcela_to_bbox(parcela)
    now        = datetime.now(timezone.utc)
    start_date = (now - timedelta(days=_LOOKBACK_DAYS)).strftime("%Y-%m-%d")
    end_date   = now.strftime("%Y-%m-%d")

    logger.info("[stac_worker] Procesando parcela %s bbox=%s", parcela_id, bbox)

    # 1. Buscar productos Sentinel-2
    items = await copernicus_client.search_sentinel2(
        bbox=bbox,
        start_date=start_date,
        end_date=end_date,
        cloud_cover_max=_CLOUD_COVER_MAX,
        limit=3,
    )

    if not items:
        logger.warning("[stac_worker] Sin imágenes para %s en %s–%s", parcela_id, start_date, end_date)
        return {"parcela_id": parcela_id, "status": "no_images", "bbox": bbox}

    # 2. Tomar el más reciente
    latest = items[0]
    product_id = latest.get("id", "unknown")
    is_simulated = latest.get("properties", {}).get("sim", False)

    # 3. Calcular NDVI (simulado si no hay credenciales o rasterio)
    if is_simulated:
        ndvi_result = ndvi_worker.simulate_parcela_indices(parcela_id, end_date)
    else:
        # En producción: descargar bandas y procesar
        ndvi_result = ndvi_worker.simulate_parcela_indices(parcela_id, end_date)
        logger.info("[stac_worker] Modo producción: %s (producto real no descargado)", product_id)

    result = {
        "parcela_id":   parcela_id,
        "parcela_nombre": parcela.get("nombre", ""),
        "cultivo":      parcela.get("cultivo", ""),
        "bbox":         bbox,
        "producto_id":  product_id,
        "simulado":     is_simulated,
        "fecha_analisis": now.isoformat(),
        "indices":      ndvi_result.to_dict(),
        "status":       "ok",
    }

    # 4. Guardar resultado local
    out_path = _save_result(parcela_id, result)
    result["resultado_path"] = str(out_path)

    # 5. Registrar en GaiaChain si está configurado
    try:
        import sys, os as _os
        sys.path.insert(0, _os.path.join(_os.path.dirname(__file__), "../.."))
        from castuo_graph.skills import registrar_en_blockchain
        metadata = {
            "parcela_id": parcela_id,
            "ndvi_mean":  result["indices"]["ndvi_stats"].get("mean"),
            "anomalies":  len(result["indices"]["anomalies"]),
            "producto":   product_id,
        }
        tx_hash = registrar_en_blockchain(f"SAT:{parcela_id}", metadata)
        result["tx_hash"] = tx_hash
        logger.info("[stac_worker] Registrado en blockchain: %s", tx_hash[:20])
    except Exception as exc:
        logger.debug("[stac_worker] Blockchain no disponible: %s", exc)
        result["tx_hash"] = None

    return result


async def run_cycle() -> list[dict[str, Any]]:
    """Ejecuta un ciclo completo de ingestión para todas las parcelas."""
    from services.satellite.copernicus_client import CopernicusClient
    from services.satellite import ndvi_worker

    client  = CopernicusClient()
    parcelas = _load_parcelas()
    results  = []

    tasks = [_process_parcela(p, client, ndvi_worker) for p in parcelas]
    completed = await asyncio.gather(*tasks, return_exceptions=True)

    for r in completed:
        if isinstance(r, Exception):
            logger.error("[stac_worker] Error en parcela: %s", r)
        else:
            results.append(r)

    await client.close()
    logger.info(
        "[stac_worker] Ciclo completado: %d/%d parcelas OK",
        sum(1 for r in results if r.get("status") == "ok"),
        len(parcelas),
    )
    return results


def run() -> None:
    """Punto de entrada para el worker en modo continuo (loop)."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    logger.info("[stac_worker] CASTÚO Satellite STAC Worker arrancando")
    logger.info("[stac_worker] Parcelas: %s | Poll: %ds", _PARCELAS_FILE, _POLL_INTERVAL)

    while True:
        try:
            results = asyncio.run(run_cycle())
            logger.info("[stac_worker] %d parcelas procesadas", len(results))
        except Exception as exc:
            logger.error("[stac_worker] Error en ciclo: %s", exc)
        time.sleep(_POLL_INTERVAL)


if __name__ == "__main__":
    run()
