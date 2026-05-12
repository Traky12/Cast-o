from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from services.blockchain.evidence_register import EvidenceRegistrar


class FakeEvidenceBackend:
    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    def create(self, payload: dict[str, Any]) -> dict[str, Any]:
        self.calls.append(payload)
        return {
            "txid": "0xabc123",
            "timestamp": "2026-04-02T10:00:00Z",
        }


def test_compute_asset_hash_is_stable(tmp_path: Path) -> None:
    sample = tmp_path / "asset.bin"
    sample.write_bytes(b"castuo-satellite-data")

    registrar = EvidenceRegistrar(backend=FakeEvidenceBackend())

    first = registrar.compute_asset_hash(str(sample))
    second = registrar.compute_asset_hash(str(sample))

    assert first == second
    assert len(first) == 64


def test_register_asset_returns_traceability_payload(tmp_path: Path) -> None:
    sample = tmp_path / "ndvi.tif"
    sample.write_bytes(b"binary-raster")
    backend = FakeEvidenceBackend()
    registrar = EvidenceRegistrar(backend=backend)

    result = registrar.register_asset(
        asset_path=str(sample),
        metadata={"parcel_id": "parcel_1", "source": "copernicus"},
    )

    assert result["txid"] == "0xabc123"
    assert result["asset"] == str(sample)
    assert result["metadata"]["parcel_id"] == "parcel_1"
    assert "hash" in result
    assert backend.calls[0]["asset"] == str(sample)


def test_register_asset_without_backend_uses_local_fallback(tmp_path: Path) -> None:
    sample = tmp_path / "ndmi.tif"
    sample.write_bytes(b"binary-raster-2")

    registrar = EvidenceRegistrar(backend=None)
    result = registrar.register_asset(asset_path=str(sample), metadata={"test": True})

    assert result["txid"].startswith("local-")
    ts = datetime.fromisoformat(result["timestamp"].replace("Z", "+00:00")).astimezone(timezone.utc)
    assert ts is not None
    assert "hash" in result
    assert result["asset"] == str(sample)
