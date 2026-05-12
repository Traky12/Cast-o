import json
import logging
from typing import Any, Dict, List

from web3 import Web3

from ..config import settings


logger = logging.getLogger(__name__)

w3 = Web3(Web3.HTTPProvider(settings.GAIA_CHAIN_RPC))
contract_address = settings.GAIA_CHAIN_AUDIT_CONTRACT
contract_abi = json.loads(settings.GAIA_CHAIN_AUDIT_ABI)
contract = w3.eth.contract(address=contract_address, abi=contract_abi)


def get_audit_trail_from_chain(token_id: int) -> List[Dict[str, Any]]:
  """Obtiene el trail de auditoría desde GaiaChain."""
  try:
    events = contract.functions.getAuditTrail(token_id).call()
    parsed: List[Dict[str, Any]] = []
    for ev in events:
      parsed.append(
        {
          "timestamp": ev[0],
          "action": ev[1],
          "status": ev[2],
          "details": json.loads(ev[3]) if ev[3] else {},
          "transactionHash": ev[4],
          "registeredBy": ev[5],
        }
      )
    return parsed
  except Exception as exc:
    logger.error("Error obteniendo trail de GaiaChain: %s", exc)
    raise


def register_event_in_chain(event_data: Dict[str, Any]) -> str:
  """Registra un evento en el contrato de auditoría de GaiaChain."""
  try:
    private_key = settings.GAIA_CHAIN_PRIVATE_KEY
    account = w3.eth.account.from_key(private_key.replace("0x", "").strip())
    tx = contract.functions.registerEvent(
      int(event_data["tokenId"]),
      event_data["action"],
      event_data["status"],
      json.dumps(event_data.get("details", {})),
      json.dumps(event_data.get("compliance", {})),
    ).build_transaction(
      {
        "from": account.address,
        "gas": 500000,
        "gasPrice": w3.to_wei("50", "gwei"),
        "nonce": w3.eth.get_transaction_count(account.address),
      }
    )
    signed = account.sign_transaction(tx)
    tx_hash_bytes = w3.eth.send_raw_transaction(signed.rawTransaction)
    return tx_hash_bytes.hex()
  except Exception as exc:
    logger.error("Error registrando evento en GaiaChain: %s", exc)
    raise

