"""
Validación local de GeoJSON exportado manualmente desde el visor SIGPAC (sin API REST ficticia).
Área en ha: con GDAL, WGS84 (RFC 7946) → EPSG:25830 salvo que el Feature declare CRS proyectado (p. ej. 25830).
Sin GDAL: solo estructura topológica básica (sin superficie UTM).

GaiaChain: register_event_in_chain(event_data: dict) — un único dict con tokenId, action, status,
details (objeto), compliance (objeto). Nunca kwargs sueltos. Opcional: env CASTUO_SIGPAC_AUDIT_TOKEN_ID.
"""
from __future__ import annotations

import json
import logging
import os
from typing import Any, Dict, List, Optional, Tuple, Union

logger = logging.getLogger(__name__)

try:
    from osgeo import ogr, osr

    _OGR_AVAILABLE = True
except ImportError:
    ogr = None  # type: ignore[assignment, misc]
    osr = None  # type: ignore[assignment, misc]
    _OGR_AVAILABLE = False

JsonDict = Dict[str, Any]


def _ring_closed(ring: List[List[float]]) -> bool:
    if len(ring) < 4:
        return False
    return ring[0] == ring[-1]


def _validate_polygon_coordinates(coords: List[Any]) -> Tuple[bool, str]:
    if not coords or not isinstance(coords, list):
        return False, "coordinates vacías"
    outer = coords[0]
    if not isinstance(outer, list) or len(outer) < 4:
        return False, "anillo exterior inválido"
    try:
        ring = [[float(p[0]), float(p[1])] for p in outer]
    except (TypeError, ValueError, IndexError):
        return False, "puntos no numéricos"
    if not _ring_closed(ring):
        return False, "polígono no cerrado"
    return True, ""


def _structural_validate_feature(geojson_data: JsonDict) -> Tuple[bool, str]:
    if geojson_data.get("type") != "Feature":
        return False, "GeoJSON debe ser un Feature"
    geom = geojson_data.get("geometry")
    if not isinstance(geom, dict):
        return False, "Falta geometry"
    gtype = geom.get("type")
    if gtype == "Polygon":
        ok, msg = _validate_polygon_coordinates(geom.get("coordinates", []))
        return ok, msg
    if gtype == "MultiPolygon":
        for poly in geom.get("coordinates", []) or []:
            ok, msg = _validate_polygon_coordinates(poly)
            if not ok:
                return False, msg
        return True, ""
    return False, "geometry debe ser Polygon o MultiPolygon"


def _feature_crs_urn(geojson_data: JsonDict) -> str:
    crs = geojson_data.get("crs")
    if not isinstance(crs, dict):
        return ""
    props = crs.get("properties")
    if not isinstance(props, dict):
        return ""
    return str(props.get("name") or "")


def _area_ha_with_ogr(geojson_data: JsonDict) -> Tuple[Optional[float], str]:
    if not _OGR_AVAILABLE:
        return None, "GDAL/osgeo no instalado"
    assert ogr is not None and osr is not None
    geometry = geojson_data["geometry"]
    gj = json.dumps(geometry)
    geom = ogr.CreateGeometryFromJson(gj)
    if geom is None:
        logger.error("GDAL CreateGeometryFromJson falló (parcela en validación local)")
        return None, "CreateGeometryFromJson falló"
    if not geom.IsValid():
        logger.error("GDAL IsValid()=False antes de reproyección")
        return None, "IsValid()=False"

    urn = _feature_crs_urn(geojson_data)
    if "25830" in urn or "32630" in urn:
        m2 = geom.GetArea()
    else:
        srs_wgs = osr.SpatialReference()
        srs_wgs.ImportFromEPSG(4326)
        srs_utm = osr.SpatialReference()
        srs_utm.ImportFromEPSG(25830)
        tx = osr.CoordinateTransformation(srs_wgs, srs_utm)
        g2 = geom.Clone()
        try:
            tr = g2.Transform(tx)
            if isinstance(tr, int) and tr != 0:
                logger.error(
                    "Reproyección 4326→25830 devolvió código OGR %s (urn CRS=%r); "
                    "comprobar geometría fuera de uso razonable UTM30N",
                    tr,
                    urn or "(RFC7946 sin crs, asumido WGS84)",
                )
                return None, f"OGR Transform código {tr}"
        except Exception as exc:  # noqa: BLE001
            logger.exception("GDAL error en Transform 4326→25830: %s", exc)
            return None, f"reproyección fallida: {exc}"
        if not g2.IsValid():
            logger.error("Geometría inválida tras reproyección a EPSG:25830")
            return None, "geometría inválida tras reproyección"
        m2 = g2.GetArea()
    return round(m2 / 10000.0, 4), ""


def _optional_register_chain(
    parcel_id: str,
    action: str,
    status: str,
    details: JsonDict,
    *,
    compliance_refs: Optional[List[str]] = None,
) -> None:
    raw = os.environ.get("CASTUO_SIGPAC_AUDIT_TOKEN_ID", "").strip()
    if not raw:
        return
    try:
        token_id = int(raw)
    except ValueError:
        logger.warning("CASTUO_SIGPAC_AUDIT_TOKEN_ID no es entero; omitiendo cadena")
        return
    compliance: JsonDict = {"note": "sigpac_geojson_local_validation"}
    if compliance_refs:
        compliance["normative_references"] = compliance_refs
    payload: JsonDict = {
        "tokenId": token_id,
        "action": action,
        "status": status,
        "details": {"parcel_id": parcel_id, **details},
        "compliance": compliance,
    }
    try:
        from backend.api.services.gaiachain_service import register_event_in_chain

        register_event_in_chain(payload)
    except Exception as exc:  # noqa: BLE001
        logger.error(
            "Registro GaiaChain opcional fallido (sigpac): parcel_id=%s error=%s",
            parcel_id,
            exc,
            exc_info=True,
        )


class SIGPACValidator:
    """Valida geometrías descargadas manualmente; no sustituye expediente SIGPAC/MAPA."""

    def validate_geojson(self, geojson_data: JsonDict, parcel_id: str) -> JsonDict:
        try:
            return self._validate_geojson_impl(geojson_data, parcel_id)
        except Exception as exc:  # noqa: BLE001
            logger.exception("Error inesperado validación SIGPAC GeoJSON parcel_id=%s", parcel_id)
            return {
                "status": "error",
                "message": str(exc),
                "parcel_id": parcel_id,
                "compliance": ["UNE-EN ISO 19115"],
            }

    def _validate_geojson_impl(self, geojson_data: JsonDict, parcel_id: str) -> JsonDict:
        ok, err = _structural_validate_feature(geojson_data)
        if not ok:
            return {
                "status": "error",
                "message": err,
                "parcel_id": parcel_id,
                "compliance": ["UNE-EN ISO 19115"],
            }

        area_ha: Optional[float] = None
        area_note = ""

        if _OGR_AVAILABLE:
            area_ha, area_note = _area_ha_with_ogr(geojson_data)
            if area_ha is None:
                return {
                    "status": "invalid",
                    "message": area_note or "geometría inválida para OGR",
                    "parcel_id": parcel_id,
                    "compliance": ["UNE-EN ISO 19115"],
                }
        else:
            area_note = (
                "Sin GDAL: no se calcula superficie en UTM30N; instalar osgeo "
                "(requirements en backend/integrations/requirements-sigpac-gdal.txt)"
            )

        props = geojson_data.get("properties")
        has_declared_area = (
            isinstance(geojson_data.get("properties"), dict) and "area_ha" in geojson_data["properties"]
        )
        if not isinstance(props, dict):
            props = {}
        declared = props.get("area_ha") if has_declared_area else None
        if declared is not None and area_ha is not None:
            try:
                declared_f = float(declared)
                deviation = abs(area_ha - declared_f) / declared_f * 100
                if deviation > 5:
                    out = {
                        "status": "warning",
                        "message": (
                            f"Desviación de área >5% (OGR UTM30N: {area_ha:.2f} ha, "
                            f"declarada: {declared_f} ha)"
                        ),
                        "area_deviation_percent": round(deviation, 2),
                        "parcel_id": parcel_id,
                        "area_ha": area_ha,
                        "compliance": ["RD 903/2025", "UNE-EN ISO 19115"],
                    }
                    _optional_register_chain(
                        parcel_id,
                        "sigpac_geojson_local_validation",
                        "warning",
                        {"area_ha": area_ha, "deviation_percent": deviation},
                        compliance_refs=[
                            "Reglamento (UE) 2019/1009",
                            "RD 903/2025",
                            "UNE-EN ISO 19115",
                        ],
                    )
                    return out
            except (TypeError, ValueError):
                logger.warning(
                    "properties.area_ha no numérico para parcel_id=%s; se omite comparación 5%%",
                    parcel_id,
                )

        out: JsonDict = {
            "status": "valid",
            "message": "Geometría coherente (validación local)",
            "parcel_id": parcel_id,
            "compliance": ["Reglamento (UE) 2019/1009", "RD 903/2025", "UNE-EN ISO 19115"],
        }
        if area_ha is not None:
            out["area_ha"] = round(area_ha, 4)
        else:
            out["area_ha"] = None
            out["validation_note"] = area_note

        _optional_register_chain(
            parcel_id,
            "sigpac_geojson_local_validation",
            "completed",
            {"area_ha": area_ha, "structural_ok": True},
            compliance_refs=[
                "Reglamento (UE) 2019/1009",
                "RD 903/2025",
                "UNE-EN ISO 19115",
            ],
        )
        return out
