#!/usr/bin/env python3
"""
PEI-001: cruce parcelas Castúo vs capa SIGPAC local (GeoJSON o SHP).
Opcional: mapping JSON (usos_declarados, usos_sigpac, codigos_sigpac).
Sin API MAPA remota; el informe alimenta trazabilidad en /pei-001-sigpac/reports/.
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

try:
    import geopandas as gpd
    from shapely.geometry import mapping as geom_mapping

    _GEOPANDAS = True
except ImportError:
    gpd = None  # type: ignore[assignment, misc]
    geom_mapping = None  # type: ignore[assignment, misc]
    _GEOPANDAS = False

logger = logging.getLogger(__name__)

JsonDict = Dict[str, Any]
MappingSets = Tuple[Dict[str, Set[str]], Dict[str, Set[str]]]


@dataclass(frozen=True)
class ValidationConfig:
    parcel_id_field: str
    parcel_declared_field: str
    sigpac_use_field: str
    sigpac_code_field: Optional[str] = None


def _load_gdf(path: Path) -> "gpd.GeoDataFrame":
    if not _GEOPANDAS:
        raise RuntimeError(
            "geopandas no instalado. pip install -r pei-001-sigpac/scripts/requirements.txt "
            "y GDAL del sistema para shapefiles."
        )
    return gpd.read_file(path)


def _to_wgs84(gdf: "gpd.GeoDataFrame") -> "gpd.GeoDataFrame":
    if gdf.crs is None:
        return gdf.set_crs("EPSG:4326", allow_override=True)
    if gdf.crs.to_string() != "EPSG:4326":
        return gdf.to_crs("EPSG:4326")
    return gdf


def _norm_token(value: Any) -> str:
    return str(value).strip().lower()


def _parse_usos_sides(raw: JsonDict) -> MappingSets:
    def side(obj: Any, label: str) -> Dict[str, Set[str]]:
        if obj is None:
            return {}
        if not isinstance(obj, dict):
            raise ValueError(f"mapping.{label} debe ser un objeto")
        out: Dict[str, Set[str]] = {}
        for k, v in obj.items():
            nk = _norm_token(k)
            if isinstance(v, list):
                out[nk] = {_norm_token(x) for x in v}
            else:
                out[nk] = {_norm_token(v)}
        return out

    ud = side(raw.get("usos_declarados"), "usos_declarados")
    us = side(raw.get("usos_sigpac"), "usos_sigpac")
    return ud, us


def _parse_codigos_sigpac(raw: JsonDict) -> Dict[str, str]:
    cobj = raw.get("codigos_sigpac")
    if cobj is None:
        return {}
    if not isinstance(cobj, dict):
        raise ValueError("mapping.codigos_sigpac debe ser un objeto")
    return {str(k).strip(): _norm_token(v) for k, v in cobj.items()}


def load_mapping_file(path: str | Path) -> Tuple[MappingSets, Dict[str, str]]:
    """Carga mapping completo: (usos_declarados, usos_sigpac), codigos_sigpac normalizado."""
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("mapping JSON debe ser un objeto en la raiz")
    return _parse_usos_sides(raw), _parse_codigos_sigpac(raw)


def load_use_mapping(path: str | Path) -> MappingSets:
    """Retrocompatibilidad: solo lados usos (tests / callers antiguos)."""
    ms, _ = load_mapping_file(path)
    return ms


def layer_code_matches_catalog(
    uso_capa: Any,
    codigo: Any,
    codigos: Dict[str, str],
) -> Tuple[bool, Optional[str]]:
    """
    Si el codigo esta en codigos_sigpac, el uso textual de la capa debe coincidir
    con el uso canonico del catalogo (integridad capa vs codigo).
    """
    if not codigos or codigo is None or (isinstance(codigo, float) and str(codigo) == "nan"):
        return True, None
    ck = str(codigo).strip()
    if ck not in codigos:
        return True, None
    expected = codigos[ck]
    actual = _norm_token(uso_capa)
    if actual == expected:
        return True, None
    return False, "codigo_sigpac_incompatible_con_uso_capa"


def compliance_match(
    declared: Any,
    sigpac_val: Any,
    mapping: Optional[MappingSets],
) -> Tuple[bool, str]:
    d = _norm_token(declared)
    s = _norm_token(sigpac_val)
    if d == s:
        return True, "literal"
    if not mapping:
        return False, "no"
    ud, us = mapping
    if s in ud.get(d, set()):
        return True, "mapping"
    if d in us.get(s, set()):
        return True, "mapping"
    return False, "no"


def _usos_problematicos(results: List[JsonDict]) -> Dict[str, Dict[str, List[str]]]:
    nested: dict[str, dict[str, List[str]]] = defaultdict(lambda: defaultdict(list))
    for r in results:
        if r.get("cumple"):
            continue
        decl = str(r.get("uso_declarado") if r.get("uso_declarado") is not None else "")
        cod = r.get("codigo_sigpac")
        sig = r.get("uso_sigpac")
        if cod is not None and str(cod).strip() != "" and str(cod).lower() != "nan":
            sig_k = str(cod).strip()
        elif sig is None:
            sig_k = "sin_recinto"
        else:
            sig_k = str(sig)
        nested[decl][sig_k].append(str(r["parcela_id"]))
    return {dk: dict(inner) for dk, inner in nested.items()}


def validate_sigpac(
    parcelas_path: str | Path,
    sigpac_path: str | Path,
    output_report: str | Path,
    *,
    config: Optional[ValidationConfig] = None,
    pdf_path: Optional[str | Path] = None,
    mapping_path: Optional[str | Path] = None,
) -> List[JsonDict]:
    cfg = config or ValidationConfig(
        parcel_id_field="id",
        parcel_declared_field="uso_declarado",
        sigpac_use_field="uso_sigpac",
        sigpac_code_field=None,
    )
    p_parcelas = Path(parcelas_path).resolve()
    p_sigpac = Path(sigpac_path).resolve()
    p_out = Path(output_report).resolve()

    use_mapping: Optional[MappingSets] = None
    codigos_map: Dict[str, str] = {}
    p_map: Optional[Path] = None
    if mapping_path is not None:
        p_map = Path(mapping_path).resolve()
        use_mapping, codigos_map = load_mapping_file(p_map)

    parcelas = _to_wgs84(_load_gdf(p_parcelas))
    sigpac = _to_wgs84(_load_gdf(p_sigpac))

    missing_p = [c for c in (cfg.parcel_id_field, cfg.parcel_declared_field) if c not in parcelas.columns]
    if missing_p:
        raise ValueError(f"Columnas faltantes en parcelas: {missing_p}. Disponibles: {list(parcelas.columns)}")
    if cfg.sigpac_use_field not in sigpac.columns:
        raise ValueError(
            f"Columna SIGPAC '{cfg.sigpac_use_field}' no encontrada. Disponibles: {list(sigpac.columns)}"
        )
    if cfg.sigpac_code_field and cfg.sigpac_code_field not in sigpac.columns:
        raise ValueError(
            f"Columna codigo SIGPAC '{cfg.sigpac_code_field}' no encontrada. Disponibles: {list(sigpac.columns)}"
        )

    results: List[JsonDict] = []
    for _idx, row in parcelas.iterrows():
        geom_p = row.geometry
        pid = row[cfg.parcel_id_field]
        declared = row[cfg.parcel_declared_field]
        logger.info("Validando parcela %s", pid)

        overlaps = sigpac[sigpac.geometry.intersects(geom_p)]
        if overlaps.empty:
            results.append(
                {
                    "parcela_id": str(pid),
                    "uso_declarado": declared,
                    "uso_sigpac": None,
                    "codigo_sigpac": None,
                    "cumple": False,
                    "cumple_via": "no",
                    "motivo": "sin_recinto_sigpac_superpuesto",
                    "geometry": geom_mapping(geom_p),
                }
            )
            continue
        hit = overlaps.iloc[0]
        uso_s = hit[cfg.sigpac_use_field]
        code_val = hit[cfg.sigpac_code_field] if cfg.sigpac_code_field else None

        code_ok, code_motivo = layer_code_matches_catalog(uso_s, code_val, codigos_map)
        if not code_ok:
            results.append(
                {
                    "parcela_id": str(pid),
                    "uso_declarado": declared,
                    "uso_sigpac": uso_s,
                    "codigo_sigpac": code_val,
                    "cumple": False,
                    "cumple_via": "no",
                    "motivo": code_motivo,
                    "geometry": geom_mapping(geom_p),
                }
            )
            continue

        ok, via = compliance_match(declared, uso_s, use_mapping)
        row_out: JsonDict = {
            "parcela_id": str(pid),
            "uso_declarado": declared,
            "uso_sigpac": uso_s,
            "codigo_sigpac": code_val,
            "cumple": bool(ok),
            "cumple_via": via if ok else "no",
            "geometry": geom_mapping(geom_p),
        }
        results.append(row_out)

    total = len(results)
    ok_n = sum(1 for r in results if r.get("cumple"))
    pct = round(100.0 * ok_n / total, 2) if total else 0.0

    summary: JsonDict = {
        "total_parcelas": total,
        "cumple": ok_n,
        "no_cumple": total - ok_n,
        "porcentaje_cumplimiento": pct,
        "usos_problematicos": _usos_problematicos(results),
    }

    payload: JsonDict = {
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "parcelas_path": str(p_parcelas),
        "sigpac_path": str(p_sigpac),
        "mapping_path": str(p_map) if p_map else None,
        "config": {
            "parcel_id_field": cfg.parcel_id_field,
            "parcel_declared_field": cfg.parcel_declared_field,
            "sigpac_use_field": cfg.sigpac_use_field,
            "sigpac_code_field": cfg.sigpac_code_field,
        },
        "summary": summary,
        "results": results,
    }

    p_out.parent.mkdir(parents=True, exist_ok=True)
    p_out.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    if pdf_path:
        _write_pdf_summary(Path(pdf_path), payload)

    return results


def _write_pdf_summary(path: Path, payload: JsonDict) -> None:
    from fpdf import FPDF

    path.parent.mkdir(parents=True, exist_ok=True)
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=12)
    pdf.multi_cell(0, 8, "Castuo-System - Informe PEI-001 (SIGPAC local)")
    pdf.ln(4)
    pdf.set_font("Helvetica", size=10)
    s = payload.get("summary") or {}
    pdf.multi_cell(
        0,
        6,
        f"UTC: {payload.get('generated_utc')}\n"
        f"Parcelas: {s.get('total_parcelas')}\n"
        f"Cumple: {s.get('cumple')}\n"
        f"No cumple: {s.get('no_cumple')}\n"
        f"Porcentaje cumplimiento: {s.get('porcentaje_cumplimiento')}%\n",
    )
    pdf.output(str(path))


def _parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    root = Path(__file__).resolve().parents[1]
    default_parcelas = root / "tests" / "fixtures" / "parcelas_test.geojson"
    default_sigpac = root / "tests" / "fixtures" / "sigpac_layer_test.geojson"
    default_out = root / "reports" / "sigpac_pei001.json"

    p = argparse.ArgumentParser(description="PEI-001 validación SIGPAC local")
    p.add_argument("--parcelas", type=Path, default=default_parcelas)
    p.add_argument("--sigpac", type=Path, default=default_sigpac)
    p.add_argument("--out-json", type=Path, default=default_out)
    p.add_argument("--out-pdf", type=Path, default=None)
    p.add_argument(
        "--mapping-path",
        type=Path,
        default=None,
        help="JSON: usos_declarados, usos_sigpac, opcional codigos_sigpac",
    )
    p.add_argument(
        "--sigpac-code-field",
        default=None,
        help="Columna del codigo numerico SIGPAC en la capa (ej: codigo, COD_USO)",
    )
    p.add_argument("--parcel-id-field", default="id")
    p.add_argument("--parcel-declared-field", default="uso_declarado")
    p.add_argument("--sigpac-use-field", default="uso_sigpac")
    p.add_argument(
        "--verbose",
        action="store_true",
        help="Log INFO en stderr",
    )
    return p.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> int:
    args = _parse_args(argv)
    logging.basicConfig(
        level=logging.INFO if args.verbose else logging.WARNING,
        format="%(levelname)s %(name)s: %(message)s",
    )
    cfg = ValidationConfig(
        parcel_id_field=args.parcel_id_field,
        parcel_declared_field=args.parcel_declared_field,
        sigpac_use_field=args.sigpac_use_field,
        sigpac_code_field=args.sigpac_code_field,
    )
    try:
        validate_sigpac(
            args.parcelas,
            args.sigpac,
            args.out_json,
            config=cfg,
            pdf_path=args.out_pdf,
            mapping_path=args.mapping_path,
        )
    except Exception as exc:  # noqa: BLE001 — CLI: mensaje operativo
        print(f"PEI-001 error: {exc}", file=sys.stderr)
        return 2
    print(f"Informe JSON: {args.out_json.resolve()}")
    if args.out_pdf:
        print(f"Informe PDF: {args.out_pdf.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
