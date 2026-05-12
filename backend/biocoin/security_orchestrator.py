"""
Orquestador cripto-físico BioCoin Castuo: vinculación chip (Secure Element) ↔ blockchain.

EvidenceHash ancla biomasa ↔ bit: NIR (tinta) + digest GNSS cosecha; piezo opcional sella tamper físico.
HSM Shamir 3/5 off-chain; on-chain solo ecrecover del oráculo.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any

try:
    from eth_account.messages import encode_defunct
    from eth_account import Account
except ImportError:
    encode_defunct = None
    Account = None


def harvest_geolocation_digest(latitude_deg: float, longitude_deg: float, decimals: int = 5) -> str:
    """
    Hash estable de parcela (WGS84); el redondeo limita fuga de precisión milimétrica en cadena.
    Sustituye o complementa geohash legible según política de privacidad del lote.
    """
    lat = round(float(latitude_deg), decimals)
    lon = round(float(longitude_deg), decimals)
    raw = f"CASTUO_HARVEST|WGS84|{lat:.{decimals}f}|{lon:.{decimals}f}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def compute_evidence_hash(
    serial_id: str,
    nir_spectral_fingerprint_b64: str,
    harvest_geohash_or_coord_hash: str,
    *,
    piezo_baseline_normalized: str | None = None,
    ald_chlorella_color_ref: str | None = None,
) -> bytes:
    """
    Registro vivo: firma espectral NIR + ancla territorial cosecha.
    piezo_*: línea base óhmica post-acuñación; taladro/extracción chip altera red → nuevo scan no encaja.
    ald_*: referencia colorimétrica protegida por capa PVD/ALD (coherencia app móvil).
    """
    parts = [
        serial_id.strip().upper(),
        nir_spectral_fingerprint_b64.strip(),
        harvest_geohash_or_coord_hash.strip(),
    ]
    if piezo_baseline_normalized:
        parts.append(f"PIEZO:{piezo_baseline_normalized.strip()}")
    if ald_chlorella_color_ref:
        parts.append(f"ALD:{ald_chlorella_color_ref.strip()}")
    payload = "|".join(parts)
    return hashlib.sha256(payload.encode("utf-8")).digest()


def evidence_score_from_layers(
    nir_match_score_0_1: float,
    piezo_integrity_ok: bool,
    ald_color_coherence_0_1: float,
) -> int:
    """
    Score 0–10000 (BPS) para dashboard / umbral recompra bioReserve.
    Piezo roto anula confianza física (tamper-evident).
    """
    if not piezo_integrity_ok:
        return 0
    base = 0.45 * nir_match_score_0_1 + 0.35 * ald_color_coherence_0_1 + 0.2
    return max(0, min(10_000, int(round(base * 10_000))))


def evidence_hash_hex(
    serial_id: str,
    nir_spectral_fingerprint_b64: str,
    harvest_geohash_or_coord_hash: str,
    *,
    piezo_baseline_normalized: str | None = None,
    ald_chlorella_color_ref: str | None = None,
) -> str:
    return "0x" + compute_evidence_hash(
        serial_id,
        nir_spectral_fingerprint_b64,
        harvest_geohash_or_coord_hash,
        piezo_baseline_normalized=piezo_baseline_normalized,
        ald_chlorella_color_ref=ald_chlorella_color_ref,
    ).hex()


def build_manifest_canonical(
    serial_id: str,
    place_of_mint: str,
    mold_temp_c: float,
    production_ts_iso: str | None = None,
    lca_co2_kg_snapshot: float | None = None,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """JSON canónico firmado por fabricante (telemetría moldeo + LCA)."""
    ts = production_ts_iso or datetime.now(timezone.utc).isoformat()
    manifest: dict[str, Any] = {
        "schema": "castuo.biocoin.manifest.v1",
        "serial_id": serial_id,
        "place_of_mint": place_of_mint,
        "mold_temperature_c": round(float(mold_temp_c), 2),
        "production_timestamp": ts,
    }
    if lca_co2_kg_snapshot is not None:
        manifest["lca_co2_kg_negatif_snapshot"] = round(float(lca_co2_kg_snapshot), 4)
    if extra:
        manifest["extensions"] = extra
    return manifest


def manifest_canonical_hash(manifest: dict[str, Any]) -> str:
    canonical = json.dumps(manifest, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return "0x" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def sign_manifest_for_mint(
    manifest: dict[str, Any],
    oracle_private_key_hex: str,
) -> str:
    """Firma EIP-191 del hash del manifest (rol oráculo HSM / custodio)."""
    if Account is None or encode_defunct is None:
        raise RuntimeError("Instalar eth-account: pip install eth-account")
    h = manifest_canonical_hash(manifest)
    msg = encode_defunct(hexstr=h)
    pk = oracle_private_key_hex.strip()
    if pk.startswith("0x"):
        pk = pk[2:]
    acct = Account.from_key(pk)
    signed = acct.sign_message(msg)
    return signed.signature.hex()


def verify_mint_payload(
    manifest: dict[str, Any],
    evidence_hash_hex_str: str,
    oracle_signature_hex: str,
    oracle_address: str,
) -> tuple[bool, str]:
    """
    Verifica coherencia manifest + evidence antes de llamar mintWithEvidence on-chain.
    oracle_address: custodio 1-of-N o clave pública del oráculo autorizado.
    """
    if Account is None or encode_defunct is None:
        return False, "eth_account_no_instalado"
    try:
        h = manifest_canonical_hash(manifest)
        msg = encode_defunct(hexstr=h)
        sig = bytes.fromhex(oracle_signature_hex.replace("0x", ""))
        recovered = Account.recover_message(msg, signature=sig)
        if recovered.lower() != oracle_address.lower():
            return False, "firma_oraculo_no_coincide"
        ev = evidence_hash_hex_str.strip().lower()
        if not ev.startswith("0x") or len(ev) != 66:
            return False, "evidence_hash_invalido"
        return True, "ok"
    except Exception as e:
        return False, str(e)


def shamir_hint_threshold() -> dict[str, Any]:
    """Documentación operativa Shamir 3/5 (implementación en HSM/Vault, no en repo)."""
    return {
        "scheme": "Shamir Secret Sharing",
        "threshold": 3,
        "shares": 5,
        "usage": "Reconstruir clave de firma de oráculo solo en entorno acreditado",
    }
