# -*- coding: utf-8 -*-
"""Servicio GaiaChain: registro inmutable según EPCIS 2.0 (blockchain)."""
from __future__ import annotations

import json
import os
from datetime import datetime
from typing import Any, Dict, List

REDIS_KEY_PENDING = "pending_blockchain_tx"


def _get_web3():
    try:
        from web3 import Web3
        return Web3
    except ImportError:
        return None


def _get_redis():
    """Cliente Redis opcional para modo degradado (cola de transacciones pendientes)."""
    try:
        import redis
        url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        return redis.from_url(url)
    except ImportError:
        return None


class GaiaChainService:
    """Registro de lotes en GaiaChain con metadatos completos. Modo degradado vía Redis."""

    def __init__(self) -> None:
        rpc = os.getenv("GAIA_CHAIN_RPC", "")
        self._rpc = rpc
        self._contract_address = os.getenv("GAIA_CHAIN_CONTRACT", "")
        abi_str = os.getenv("GAIA_CHAIN_ABI", "[]")
        self._abi = json.loads(abi_str) if abi_str else []
        self._private_key = os.getenv("GAIA_CHAIN_PRIVATE_KEY", "")
        self._chain_id = int(os.getenv("GAIA_CHAIN_CHAIN_ID", "1337"))
        self._w3 = None
        self._contract = None
        self._account = None
        self._redis = _get_redis()
        if rpc and self._contract_address and self._abi and self._private_key:
            Web3 = _get_web3()
            if Web3:
                self._w3 = Web3(Web3.HTTPProvider(rpc))
                self._contract = self._w3.eth.contract(
                    address=self._w3.to_checksum_address(self._contract_address),
                    abi=self._abi,
                )
                self._account = self._w3.eth.account.from_key(self._private_key)

    def _is_connected(self) -> bool:
        """Comprueba si la conexión a GaiaChain está operativa."""
        if not self._w3:
            return False
        try:
            return self._w3.is_connected()
        except Exception:
            return False

    def _push_pending(self, batch_data: Dict[str, Any]) -> None:
        """Encola transacción en Redis para sincronización posterior (modo degradado)."""
        if self._redis:
            self._redis.rpush(REDIS_KEY_PENDING, json.dumps(batch_data, default=str))

    async def register_batch(
        self,
        batch_data: Dict[str, Any],
        *,
        _sync_mode: bool = False,
    ) -> Dict[str, Any]:
        """Registra un lote en GaiaChain. Si falla y no _sync_mode, encola en Redis (modo degradado)."""
        def queue_if_not_sync():
            if not _sync_mode:
                self._push_pending(batch_data)

        if not self._w3 or not self._contract or not self._account:
            stub = self._stub_register(batch_data)
            queue_if_not_sync()
            return {**stub, "status": "degraded", "message": "Transaction queued for sync"}
        if not self._is_connected():
            queue_if_not_sync()
            return {
                "status": "degraded",
                "message": "GaiaChain unreachable; transaction queued for later sync",
                "transaction_hash": None,
            }
        try:
            tx = self._contract.functions.registerBatch(
                batch_data["batch_id"],
                batch_data.get("strain_id", ""),
                int(float(batch_data.get("thc_percentage", 0)) * 100),
                int(float(batch_data.get("cbd_percentage", 0)) * 100),
                int(float(batch_data.get("weight_kg", 0)) * 1000),
                json.dumps(batch_data.get("lab_results", {})),
                batch_data.get("account_id", ""),
                int(datetime.now().timestamp()),
            ).build_transaction({
                "chainId": self._chain_id,
                "gas": 2000000,
                "gasPrice": self._w3.to_wei(1, "gwei"),
                "nonce": self._w3.eth.get_transaction_count(self._account.address),
            })
            signed_tx = self._w3.eth.account.sign_transaction(tx, self._private_key)
            tx_hash = self._w3.eth.send_raw_transaction(signed_tx.raw_transaction)
            receipt = self._w3.eth.wait_for_transaction_receipt(tx_hash)
            return {
                "transaction_hash": tx_hash.hex(),
                "block_number": receipt["blockNumber"],
                "status": "confirmed",
            }
        except Exception as e:
            self._push_pending(batch_data)
            return {
                "status": "degraded",
                "message": str(e),
                "transaction_hash": None,
            }

    def _stub_register(self, batch_data: Dict[str, Any]) -> Dict[str, Any]:
        """Stub cuando GaiaChain no está configurado."""
        import hashlib
        payload = (
            f"{batch_data.get('batch_id', '')}:"
            f"{batch_data.get('strain_id', '')}:"
            f"{datetime.now().isoformat()}"
        )
        tx_hash = "0x" + hashlib.sha256(payload.encode()).hexdigest()
        return {
            "transaction_hash": tx_hash,
            "block_number": 0,
            "status": "confirmed",
            "message": "Stub (configure GAIA_CHAIN_* for real chain)",
        }

    def get_pending_count(self) -> int:
        """Número de transacciones pendientes en cola (Redis)."""
        if not self._redis:
            return 0
        return self._redis.llen(REDIS_KEY_PENDING)

    def get_pending_batches(self) -> List[Dict[str, Any]]:
        """Devuelve la lista de lotes pendientes de registrar (sin sacarlos de la cola)."""
        if not self._redis:
            return []
        raw = self._redis.lrange(REDIS_KEY_PENDING, 0, -1)
        out = []
        for r in raw or []:
            try:
                out.append(json.loads(r))
            except json.JSONDecodeError:
                pass
        return out

    async def sync_pending_transactions(self) -> Dict[str, Any]:
        """Sincroniza transacciones pendientes con GaiaChain (recuperación tras caída)."""
        if not self._redis:
            return {"synced": 0, "failed": 0, "message": "Redis not configured"}
        synced = 0
        failed = 0
        while self._redis.llen(REDIS_KEY_PENDING) > 0 and self._is_connected():
            raw = self._redis.lpop(REDIS_KEY_PENDING)
            if not raw:
                break
            try:
                batch_data = json.loads(raw)
            except json.JSONDecodeError:
                failed += 1
                continue
            result = await self.register_batch(batch_data, _sync_mode=True)
            if result.get("status") == "confirmed":
                synced += 1
            else:
                self._redis.rpush(REDIS_KEY_PENDING, raw)
                failed += 1
                break
        return {"synced": synced, "failed": failed, "pending": self.get_pending_count()}
