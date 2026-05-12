from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from validate_sigpac import (  # noqa: E402
    ValidationConfig,
    compliance_match,
    layer_code_matches_catalog,
    load_mapping_file,
    load_use_mapping,
    validate_sigpac,
)


@pytest.fixture
def sample_paths(tmp_path: Path) -> dict:
    parcelas = ROOT / "tests" / "fixtures" / "parcelas_test.geojson"
    sigpac = ROOT / "tests" / "fixtures" / "sigpac_layer_test.geojson"
    out = tmp_path / "out.json"
    return {"parcelas_path": parcelas, "sigpac_path": sigpac, "output_report": out}


def test_validate_sigpac_writes_json_and_results(sample_paths: dict) -> None:
    results = validate_sigpac(
        sample_paths["parcelas_path"],
        sample_paths["sigpac_path"],
        sample_paths["output_report"],
        config=ValidationConfig(
            parcel_id_field="id",
            parcel_declared_field="uso_declarado",
            sigpac_use_field="uso_sigpac",
            sigpac_code_field="codigo_sigpac",
        ),
    )
    assert sample_paths["output_report"].exists()
    raw = json.loads(sample_paths["output_report"].read_text(encoding="utf-8"))
    assert raw["summary"]["total_parcelas"] == 2
    assert raw["summary"]["porcentaje_cumplimiento"] == 50.0
    prob = raw["summary"]["usos_problematicos"]
    assert "agrovoltaica" in prob
    assert "111" in prob["agrovoltaica"]
    assert "CASTUO-002" in prob["agrovoltaica"]["111"]
    assert len(results) == 2
    by_id = {r["parcela_id"]: r for r in results}
    assert by_id["CASTUO-001"]["cumple"] is True
    assert by_id["CASTUO-001"]["codigo_sigpac"] == "111"
    assert by_id["CASTUO-001"]["cumple_via"] == "literal"
    assert by_id["CASTUO-002"]["cumple"] is False
    assert raw["mapping_path"] is None


def test_validate_sigpac_mapping_allows_equivalence(tmp_path: Path) -> None:
    parcelas = ROOT / "tests" / "fixtures" / "parcelas_mapping_test.geojson"
    sigpac = ROOT / "tests" / "fixtures" / "sigpac_layer_test.geojson"
    mpath = ROOT / "tests" / "fixtures" / "mapping_test.json"
    out = tmp_path / "mapped.json"
    results = validate_sigpac(
        parcelas,
        sigpac,
        out,
        config=ValidationConfig(
            parcel_id_field="id",
            parcel_declared_field="uso_declarado",
            sigpac_use_field="uso_sigpac",
            sigpac_code_field="codigo_sigpac",
        ),
        mapping_path=mpath,
    )
    raw = json.loads(out.read_text(encoding="utf-8"))
    assert len(results) == 1
    assert results[0]["cumple"] is True
    assert results[0]["cumple_via"] == "mapping"
    assert raw["summary"]["porcentaje_cumplimiento"] == 100.0
    assert Path(raw["mapping_path"]).resolve() == mpath.resolve()


def test_code_mismatch_fails(tmp_path: Path) -> None:
    from validate_sigpac import ValidationConfig

    parcelas = ROOT / "tests" / "fixtures" / "parcelas_test.geojson"
    bad = ROOT / "tests" / "fixtures" / "sigpac_layer_code_mismatch.geojson"
    mpath = ROOT / "tests" / "fixtures" / "mapping_test.json"
    out = tmp_path / "bad.json"
    results = validate_sigpac(
        parcelas,
        bad,
        out,
        mapping_path=mpath,
        config=ValidationConfig(
            parcel_id_field="id",
            parcel_declared_field="uso_declarado",
            sigpac_use_field="uso_sigpac",
            sigpac_code_field="codigo_sigpac",
        ),
    )
    assert all(
        r.get("motivo") == "codigo_sigpac_incompatible_con_uso_capa" for r in results if not r["cumple"]
    )


def test_data_mapping_with_fixtures(tmp_path: Path) -> None:
    """Sanidad: pei-001-sigpac/data/mapping.json coherente con fixtures de prueba."""
    mpath = ROOT / "data" / "mapping.json"
    out = tmp_path / "dm.json"
    validate_sigpac(
        ROOT / "tests" / "fixtures" / "parcelas_mapping_test.geojson",
        ROOT / "tests" / "fixtures" / "sigpac_layer_test.geojson",
        out,
        mapping_path=mpath,
        config=ValidationConfig(
            parcel_id_field="id",
            parcel_declared_field="uso_declarado",
            sigpac_use_field="uso_sigpac",
            sigpac_code_field="codigo_sigpac",
        ),
    )
    raw = json.loads(out.read_text(encoding="utf-8"))
    assert raw["results"][0]["cumple"] is True


def test_compliance_match_without_file() -> None:
    ok, via = compliance_match("a", "a", None)
    assert ok and via == "literal"
    ok, via = compliance_match("a", "b", None)
    assert not ok and via == "no"


def test_compliance_match_with_mapping() -> None:
    ms = load_use_mapping(ROOT / "tests" / "fixtures" / "mapping_test.json")
    ok, via = compliance_match("cannabis_medicinal", "cultivo_herbaceo", ms)
    assert ok and via == "mapping"
    ok, via = compliance_match("otro", "cultivo_herbaceo", ms)
    assert not ok


def test_layer_code_catalog() -> None:
    _, cod = load_mapping_file(ROOT / "data" / "mapping.json")
    ok, _ = layer_code_matches_catalog("cultivo_herbaceo", "111", cod)
    assert ok
    ok, msg = layer_code_matches_catalog("barbecho", "111", cod)
    assert not ok and msg == "codigo_sigpac_incompatible_con_uso_capa"


def test_validate_sigpac_pdf(tmp_path: Path) -> None:
    parcelas = ROOT / "tests" / "fixtures" / "parcelas_test.geojson"
    sigpac = ROOT / "tests" / "fixtures" / "sigpac_layer_test.geojson"
    out_j = tmp_path / "r.json"
    out_p = tmp_path / "r.pdf"
    validate_sigpac(
        parcelas,
        sigpac,
        out_j,
        pdf_path=out_p,
        config=ValidationConfig(
            parcel_id_field="id",
            parcel_declared_field="uso_declarado",
            sigpac_use_field="uso_sigpac",
            sigpac_code_field="codigo_sigpac",
        ),
    )
    assert out_p.exists()
    assert out_p.stat().st_size > 0
