# -*- coding: utf-8 -*-
"""
Cliente para contrato MaterialCertification (BioCoin Castúo).
En producción: desplegar MaterialCertification.sol y configurar CONTRACT_ADDRESS + RPC.
"""
from __future__ import annotations

import hashlib
import json
import os
from typing import List, Optional

# Opcional: from web3 import Web3

CONTRACT_ADDRESS = os.environ.get("MATERIAL_CERTIFICATION_CONTRACT", "")
RPC_URL = os.environ.get("ETHEREUM_RPC_URL", "http://localhost:8545")


def _tx_stub(prefix: str, *parts) -> str:
    data = f"{prefix}-" + "-".join(str(p) for p in parts)
    return "0x" + hashlib.sha256(data.encode()).hexdigest()[:40]


class MaterialBlockchain:
    """Interacción con MaterialCertification.sol (stub si no hay Web3)."""

    def __init__(self, rpc_url: str = None, contract_address: str = None):
        self.rpc_url = rpc_url or RPC_URL
        self.contract_address = contract_address or CONTRACT_ADDRESS
        self._w3 = None
        self._contract = None
        if self.contract_address and self._init_web3():
            pass  # contrato listo

    def _init_web3(self) -> bool:
        try:
            from web3 import Web3
            self._w3 = Web3(Web3.HTTPProvider(self.rpc_url))
            if not self._w3.is_connected():
                return False
            # Cargar ABI desde contracts/ o env
            abi_path = os.path.join(
                os.path.dirname(__file__), "..", "..", "contracts", "MaterialCertification.abi.json"
            )
            if os.path.exists(abi_path):
                with open(abi_path) as f:
                    abi = json.load(f)
                self._contract = self._w3.eth.contract(
                    address=Web3.to_checksum_address(self.contract_address),
                    abi=abi,
                )
                return True
        except Exception:
            pass
        return False

    def registrar_produccion(
        self,
        material_id: int,
        kg_producidos: float,
        raw_material_kg: float = 0.0,
        energy_kwh: float = 0.0,
        material_type: str = "hemp_composite",
        certification_body: str = "UNE",
        date: str = "",
        validity: str = "",
        ipfs_hash: str = "",
    ) -> str:
        """Registra un lote de producción en blockchain."""
        if self._contract:
            tx = self._contract.functions.registerCertification(
                material_type,
                int(kg_producidos * 1000),  # precisión
                "hemp",
                int(energy_kwh * 1000),
                certification_body,
                date or "2026-01-01",
                validity or "2027-01-01",
                ipfs_hash,
            ).transact()
            return tx.hex()
        return _tx_stub("prod", material_id, kg_producidos, raw_material_kg)

    def registrar_venta(
        self,
        sale_id: int,
        partner_id: int,
        material_ids: List[int],
        kg_sold: List[float],
        date: str = "",
        buyer_address: str = None,
    ) -> str:
        """Registra una venta."""
        if self._contract and buyer_address:
            ids = [x for x in material_ids]
            kgs = [int(k * 1000) for k in kg_sold]
            tx = self._contract.functions.registerSale(
                self._w3.to_checksum_address(buyer_address),
                ids,
                kgs,
                date or "2026-01-01",
            ).transact()
            return tx.hex()
        return _tx_stub("sale", sale_id, partner_id, len(material_ids))

    def subir_a_ipfs(self, documento_path: str) -> Optional[str]:
        """Sube documento a IPFS (requiere ipfshttpclient y nodo IPFS)."""
        try:
            import ipfshttpclient
            client = ipfshttpclient.connect("/dns/localhost/tcp/5001/http")
            with open(documento_path, "rb") as f:
                result = client.add(f)
            return result.get("Hash")
        except Exception:
            return None
