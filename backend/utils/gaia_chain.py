from pathlib import Path
import json

from web3 import Web3


class GaiaChainAuditClient:
    def __init__(self, rpc_url: str, private_key: str, contract_address: str):
        self.w3 = Web3(Web3.HTTPProvider(rpc_url))
        self.account = self.w3.eth.account.from_key(private_key)
        self.contract_address = Web3.to_checksum_address(contract_address)

        # ABI desde contracts/GaiaChainAudit.json (raíz del proyecto)
        contracts_path = (
            Path(__file__).resolve().parents[2] / "contracts" / "GaiaChainAudit.json"
        )
        with open(contracts_path, "r", encoding="utf-8") as f:
            abi = json.load(f)["abi"]

        self.contract = self.w3.eth.contract(address=self.contract_address, abi=abi)

    def get_consent_status(self, token_id: str):
        """Lee estado del contrato de auditoría de consentimientos."""
        # Ejemplo: suponemos que el contrato tiene getConsentStatus y consentHistory
        status = self.contract.functions.getConsentStatus(
            bytes.fromhex(token_id)
        ).call()
        latest_tx = self.contract.functions.consentHistory(token_id, 0).call()

        return {
            "status": "granted" if status else "pending",
            "tx_hash": latest_tx[1].hex() if latest_tx[1] else None,
            "block_number": latest_tx[0],
            "timestamp": "2026-03-16T15:18:00Z",
            # "audit_trail": [...]  # Se puede ampliar cuando el contrato lo soporte
        }

