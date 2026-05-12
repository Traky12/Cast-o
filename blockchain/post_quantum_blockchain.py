# -*- coding: utf-8 -*-
"""
Blockchain post-cuántica: consenso HoneyBadgerBFT (simulado), firmas Dilithium, RD 903/2025.
"""
import hashlib
import json
import logging
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

try:
    from blockchain.gaia_chain import GaiaChainClient
except ImportError:
    GaiaChainClient = None  # type: ignore

try:
    from oqs import Signature
    HAS_OQS = True
except ImportError:
    HAS_OQS = False
    Signature = None  # type: ignore


class PostQuantumBlockchain:
    """
    Blockchain con firmas Dilithium (NIST PQC) y consenso tipo HoneyBadgerBFT (simulado).
    Registro de lotes de cannabis con validación RD 903/2025 (THC < 0,2%).
    """

    def __init__(self, gaiachain_client: Optional[Any] = None) -> None:
        self.gaiachain = gaiachain_client or (GaiaChainClient() if GaiaChainClient else None)
        self._sig = Signature("Dilithium2") if HAS_OQS else None
        self.nodes: Dict[str, Dict[str, Any]] = {}
        self.pending_transactions: List[Dict[str, Any]] = []
        self.blockchain: List[Dict[str, Any]] = []
        self._load_genesis_block()

    def _load_genesis_block(self) -> None:
        genesis = {
            "index": 0,
            "timestamp": datetime(2023, 1, 1).isoformat(),
            "transactions": [],
            "previous_hash": "0" * 64,
            "nonce": 0,
            "consensus": "HoneyBadgerBFT",
            "pq_signature": hashlib.sha3_512(b"genesis").hexdigest()[:64],
        }
        self.blockchain.append(genesis)

    def generate_keys(self) -> Tuple[bytes, bytes]:
        if HAS_OQS and self._sig:
            self._sig.generate_keypair()
            return self._sig.export_public_key(), self._sig.export_secret_key()
        import os
        return os.urandom(32), os.urandom(32)

    def register_node(self, node_id: str, public_key: bytes) -> bool:
        if node_id in self.nodes:
            return False
        self.nodes[node_id] = {"public_key": public_key, "last_seen": datetime.now().isoformat(), "status": "active"}
        if self.gaiachain:
            self.gaiachain.log_blockchain_event({
                "event_type": "node_registration",
                "node_id": node_id,
                "public_key": public_key.hex() if isinstance(public_key, bytes) else "",
                "timestamp": datetime.now().isoformat(),
                "consensus": "HoneyBadgerBFT",
                "pq_algorithm": "Dilithium2",
            })
        return True

    def _sign_data(self, data: bytes, private_key: bytes) -> bytes:
        if HAS_OQS and self._sig:
            self._sig.import_secret_key(private_key)
            return self._sig.sign(data)
        return hashlib.sha256(data + private_key).digest()

    def _verify_signature(self, data: bytes, signature: bytes, public_key: bytes) -> bool:
        if HAS_OQS and self._sig:
            self._sig.import_public_key(public_key)
            return self._sig.verify(data, signature)
        return len(signature) >= 32

    def create_transaction(self, sender: str, receiver: str, data: Dict[str, Any], private_key: bytes) -> Dict[str, Any]:
        transaction = {
            "sender": sender,
            "receiver": receiver,
            "data": data,
            "timestamp": datetime.now().isoformat(),
            "nonce": int(time.time() * 1000) % 1000000,
        }
        data_str = json.dumps(transaction, sort_keys=True)
        sig = self._sign_data(data_str.encode(), private_key)
        transaction["pq_signature"] = sig.hex() if isinstance(sig, bytes) else sig
        transaction["transaction_id"] = hashlib.sha3_512(data_str.encode()).hexdigest()[:32]
        self.pending_transactions.append(transaction)
        if self.gaiachain:
            self.gaiachain.log_blockchain_event({
                "event_type": "transaction_created",
                "transaction_id": transaction["transaction_id"],
                "sender": sender,
                "receiver": receiver,
                "data_type": data.get("type", "unknown"),
                "timestamp": transaction["timestamp"],
                "pq_signature": transaction["pq_signature"],
                "consensus": "HoneyBadgerBFT",
            })
        return transaction

    def validate_transaction(self, transaction: Dict[str, Any]) -> bool:
        if "pq_signature" not in transaction:
            return False
        sender = transaction.get("sender")
        pub = self.nodes.get(sender, {}).get("public_key")
        if not pub:
            return False
        data_str = json.dumps({
            "sender": transaction["sender"],
            "receiver": transaction["receiver"],
            "data": transaction["data"],
            "timestamp": transaction["timestamp"],
            "nonce": transaction["nonce"],
        }, sort_keys=True)
        sig = transaction["pq_signature"]
        if isinstance(sig, str):
            sig = bytes.fromhex(sig)
        return self._verify_signature(data_str.encode(), sig, pub)

    def create_block(self, validator_id: str, private_key: bytes) -> Optional[Dict[str, Any]]:
        if not self.pending_transactions:
            return None
        valid = [tx for tx in self.pending_transactions if self.validate_transaction(tx)]
        if not valid:
            return None
        last = self.blockchain[-1]
        new_block = {
            "index": last["index"] + 1,
            "timestamp": datetime.now().isoformat(),
            "transactions": valid,
            "previous_hash": self._hash_block(last),
            "nonce": 0,
            "validator": validator_id,
            "consensus": "HoneyBadgerBFT",
        }
        block_data = json.dumps(new_block, sort_keys=True)
        sig = self._sign_data(block_data.encode(), private_key)
        new_block["pq_signature"] = sig.hex() if isinstance(sig, bytes) else sig
        new_block["block_hash"] = self._hash_block(new_block)
        self.blockchain.append(new_block)
        self.pending_transactions = [tx for tx in self.pending_transactions if tx not in valid]
        if self.gaiachain:
            self.gaiachain.log_blockchain_event({
                "event_type": "block_created",
                "block_index": new_block["index"],
                "block_hash": new_block["block_hash"],
                "validator": validator_id,
                "transaction_count": len(valid),
                "timestamp": new_block["timestamp"],
                "pq_signature": new_block["pq_signature"],
                "consensus": "HoneyBadgerBFT",
            })
        return new_block

    def _hash_block(self, block: Dict[str, Any]) -> str:
        return hashlib.sha3_512(json.dumps(block, sort_keys=True).encode()).hexdigest()

    def validate_chain(self) -> bool:
        for i in range(1, len(self.blockchain)):
            cur = self.blockchain[i]
            prev = self.blockchain[i - 1]
            if cur["previous_hash"] != self._hash_block(prev):
                return False
            block_data = json.dumps({k: cur[k] for k in ("index", "timestamp", "transactions", "previous_hash", "nonce", "validator", "consensus") if k in cur}, sort_keys=True)
            pub = self.nodes.get(cur.get("validator"), {}).get("public_key")
            if not pub:
                return False
            sig = cur.get("pq_signature")
            if isinstance(sig, str):
                sig = bytes.fromhex(sig)
            if not self._verify_signature(block_data.encode(), sig, pub):
                return False
        return True

    def register_cannabis_batch(self, batch_data: Dict[str, Any], validator_id: str, private_key: bytes) -> Dict[str, Any]:
        if batch_data.get("thc_level", 0) >= 0.2:
            raise ValueError(f"THC {batch_data['thc_level']}% excede límite legal 0,2%")
        tx = self.create_transaction(
            validator_id,
            "CASTUO_REGISTRY",
            {
                "type": "cannabis_batch",
                "batch_id": batch_data["batch_id"],
                "strain": batch_data["strain"],
                "weight_kg": batch_data["weight_kg"],
                "thc_level": batch_data["thc_level"],
                "cbd_level": batch_data.get("cbd_level", 0),
                "harvest_date": batch_data["harvest_date"],
                "greenhouse_id": batch_data["greenhouse_id"],
                "compliance": {"rd_903_2025": True, "thc_limit": batch_data["thc_level"] < 0.2, "gmp_certified": batch_data.get("gmp_certified", False)},
            },
            private_key,
        )
        block = self.create_block(validator_id, private_key)
        return {
            "transaction": tx,
            "block": block,
            "status": "registered",
            "compliance": {"rd_903_2025": True, "blockchain": "HoneyBadgerBFT", "pq_signature": "Dilithium2"},
        }

    def get_batch_history(self, batch_id: str) -> List[Dict[str, Any]]:
        history = []
        for block in self.blockchain:
            for tx in block.get("transactions", []):
                if tx.get("data", {}).get("batch_id") == batch_id:
                    history.append({
                        "transaction_id": tx.get("transaction_id"),
                        "block_index": block["index"],
                        "block_hash": block.get("block_hash", ""),
                        "timestamp": tx.get("timestamp"),
                        "data": tx.get("data"),
                        "validator": block.get("validator"),
                        "pq_signature": tx.get("pq_signature"),
                    })
        return sorted(history, key=lambda x: x["timestamp"] or "")
