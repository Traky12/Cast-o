"""
Xtranet v2027.25 — núcleo hiperintegrado Edge (Ladanum / Chlorella / auditoría SHA3-512).
Orquestación sensores → defensa perimetral → activos bio → cadena de recibos local.
"""
from __future__ import annotations

import hashlib
import json
import secrets
import time
from dataclasses import asdict, dataclass, field
from typing import Any

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

SYSTEM_ID = "CASTUO-5PRO-LADANUM-2027"


def _block_payload(block: CastuoBlock) -> bytes:
    d = asdict(block)
    d.pop("hash", None)
    return json.dumps(d, sort_keys=True, separators=(",", ":")).encode("utf-8")


@dataclass
class CastuoBlock:
    index: int
    timestamp: float
    data: dict[str, Any]
    previous_hash: str
    nonce: int = 0
    hash: str = ""


class DefenseSystem:
    def __init__(self) -> None:
        self.uav_status = "READY"
        self.shield_active = False

    def scan_airspace(self) -> dict[str, Any]:
        return {"status": "CLEAN", "threat_level": 0, "uav_patrol": self.uav_status}

    def activate_antidrone(self) -> str:
        self.shield_active = True
        return "shield_active"


class BioAssetManager:
    def __init__(self) -> None:
        self.assets: dict[str, dict[str, Any]] = {}

    def mint_biocoin(self, nfc_uid: str, biomass_type: str, co2_offset: float) -> str:
        asset_id = f"BIOC-{nfc_uid}"
        self.assets[asset_id] = {
            "type": biomass_type,
            "co2_captured": co2_offset,
            "timestamp": time.time(),
        }
        return asset_id


class CastuoDAO:
    def __init__(self) -> None:
        self.blockchain: list[CastuoBlock] = []
        self._genesis()

    def _genesis(self) -> None:
        g = CastuoBlock(0, time.time(), {"msg": "genesis_castuo"}, "0")
        g.hash = hashlib.sha3_512(_block_payload(g)).hexdigest()
        self.blockchain.append(g)

    def calculate_hash(self, block: CastuoBlock) -> str:
        return hashlib.sha3_512(_block_payload(block)).hexdigest()

    def add_audit_log(self, data: dict[str, Any]) -> str:
        prev = self.blockchain[-1]
        nb = CastuoBlock(len(self.blockchain), time.time(), data, prev.hash)
        nb.hash = self.calculate_hash(nb)
        self.blockchain.append(nb)
        return nb.hash


class XtranetCore:
    def __init__(self) -> None:
        self.defense = DefenseSystem()
        self.bio_assets = BioAssetManager()
        self.dao = CastuoDAO()
        self._aes_key = AESGCM.generate_key(bit_length=256)

    def execute_hyper_automation(self, sensor_data: dict[str, Any]) -> str:
        threats = self.defense.scan_airspace()
        nfc = sensor_data.get("nfc") or f"anon-{secrets.token_hex(4)}"
        bioc_id = self.bio_assets.mint_biocoin(
            str(nfc),
            str(sensor_data.get("biomass_type", "CHLORELLA-5PRO")),
            float(sensor_data.get("co2", 0.0)),
        )
        payload = {
            "system": SYSTEM_ID,
            "security": threats,
            "asset_minted": bioc_id,
            "compliance_tag": "REG-MICA-DRAFT",
        }
        return self.dao.add_audit_log(payload)

    def seal_backup(self, plaintext: bytes, aad: bytes | None = None) -> tuple[bytes, bytes]:
        nonce = secrets.token_bytes(12)
        aes = AESGCM(self._aes_key)
        return nonce, aes.encrypt(nonce, plaintext, aad or b"")
