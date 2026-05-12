# -*- coding: utf-8 -*-
"""Microservicio Blockchain: integración GaiaChain para trazabilidad inmutable."""
from __future__ import annotations

import json
import os
from datetime import datetime
from typing import Any, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()

GAIA_CHAIN_RPC = os.getenv("GAIA_CHAIN_RPC", "https://rpc.gaia-chain.com")
GAIA_CHAIN_CONTRACT = os.getenv("GAIA_CHAIN_CONTRACT", "")
_w3: Optional[Any] = None


def _get_web3():
    global _w3
    if _w3 is not None:
        return _w3
    try:
        from web3 import Web3
        _w3 = Web3(Web3.HTTPProvider(GAIA_CHAIN_RPC))
        return _w3
    except ImportError:
        return None


class BatchData(BaseModel):
    batch_id: str
    strain_id: str
    thc_percentage: float
    cbd_percentage: float
    weight_kg: float
    lab_results: dict
    account_id: str


@router.post("/register_batch")
async def register_batch(batch_data: BatchData):
    """Registra un lote en GaiaChain (smart contract) para trazabilidad inmutable."""
    w3 = _get_web3()
    if w3 is None:
        return _register_batch_stub(batch_data)

    contract_addr = GAIA_CHAIN_CONTRACT
    abi_str = os.getenv("GAIA_CHAIN_ABI", "[]")
    wallet = os.getenv("GAIA_CHAIN_WALLET", "")
    private_key = os.getenv("GAIA_CHAIN_PRIVATE_KEY", "")

    if not contract_addr or not wallet or not private_key:
        return _register_batch_stub(batch_data)

    try:
        abi = json.loads(abi_str)
        contract = w3.eth.contract(
            address=w3.to_checksum_address(contract_addr),
            abi=abi,
        )
        tx = contract.functions.registerBatch(
            batch_data.batch_id,
            batch_data.strain_id,
            int(batch_data.thc_percentage * 100),
            int(batch_data.cbd_percentage * 100),
            int(batch_data.weight_kg * 1000),
            json.dumps(batch_data.lab_results),
            batch_data.account_id,
            int(datetime.now().timestamp()),
        ).build_transaction({
            "chainId": 1337,
            "gas": 2000000,
            "gasPrice": w3.to_wei(1, "gwei"),
            "nonce": w3.eth.get_transaction_count(wallet),
        })
        from web3 import Account
        signed = w3.eth.account.sign_transaction(tx, private_key)
        tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        return {
            "status": "success",
            "transaction_hash": tx_hash.hex(),
            "block_number": receipt["blockNumber"],
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


def _register_batch_stub(batch_data: BatchData) -> dict:
    """Stub cuando Web3/GaiaChain no está configurado (dev/test)."""
    import hashlib
    payload = f"{batch_data.batch_id}:{batch_data.strain_id}:{datetime.now().isoformat()}"
    tx_hash = "0x" + hashlib.sha256(payload.encode()).hexdigest()[:64]
    return {
        "status": "success",
        "transaction_hash": tx_hash,
        "block_number": 0,
        "message": "Stub registration (configure GAIA_CHAIN_* for real chain)",
    }


# --- GaiaChain Real witness (TRL7) ---
try:
    from blockchain.gaia_chain_real import GaiaChainReal
    _gaia_real = GaiaChainReal()
except Exception:
    try:
        from backend.services.gaia_chain_witness import GaiaChainReal
        _gaia_real = GaiaChainReal()
    except Exception:
        _gaia_real = None


class WitnessRequest(BaseModel):
    """Payload para POST /witness (trazabilidad cooperativa/parcela)."""
    data: dict
    coop_id: int


@router.post("/witness")
async def witness(witness_request: WitnessRequest):
    """Registra un testigo en GaiaChain (hash SHA256 + opcional IPFS + API witness). TRL7."""
    if _gaia_real is None:
        import hashlib
        data_hash = hashlib.sha256(json.dumps(witness_request.data, sort_keys=True).encode()).hexdigest()
        return {"ok": True, "tx_hash": data_hash, "ipfs_cid": None, "witness_response": {}, "message": "Stub (install blockchain.gaia_chain_real)"}
    result = _gaia_real.witness_transaction(witness_request.data, witness_request.coop_id)
    if not result.get("ok"):
        raise HTTPException(status_code=502, detail=result.get("error", "Witness failed"))
    return result
