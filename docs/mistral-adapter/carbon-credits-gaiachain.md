# Integración con mercados de carbono (GaiaChain 2.0)

Tokenizar el CO₂ ahorrado en GaiaChain 2.0 para créditos de carbono.

---

## Smart contract CarbonCredit.sol

Ubicación: `contracts/CarbonCredit.sol`

- **owner:** dirección que puede emitir créditos.
- **issueCredits(to, amount):** emite créditos a una dirección (solo owner).
- **getCredits(account):** devuelve el balance de créditos.
- **Evento:** `CreditIssued(to, amount)`.

---

## Registrar CO₂ ahorrado desde el backend

Ejemplo en Python (integrado en castuo-backend o como script):

```python
from web3 import Web3
import os

GAIA_CHAIN_RPC = os.getenv("GAIA_CHAIN_RPC", "https://gaiachain.castuo-system.com")
CONTRACT_ADDRESS = os.getenv("CARBON_CREDIT_CONTRACT_ADDRESS", "0x...")
PRIVATE_KEY = os.getenv("PRIVATE_KEY")

w3 = Web3(Web3.HTTPProvider(GAIA_CHAIN_RPC))
contract = w3.eth.contract(address=Web3.to_checksum_address(CONTRACT_ADDRESS), abi=[...])

def register_carbon_credits(farm_id: str, kg_co2: int) -> str:
    """Registra CO₂ ahorrado (ej: 12 kg por 288 lechugas). farm_id como address."""
    account = w3.eth.account.from_key(PRIVATE_KEY)
    tx = contract.functions.issueCredits(
        Web3.to_checksum_address(farm_id), kg_co2 * 1000
    ).build_transaction({
        "from": account.address,
        "nonce": w3.eth.get_transaction_count(account.address),
        "gas": 200000,
        "gasPrice": w3.to_wei("50", "gwei"),
    })
    signed = account.sign_transaction(tx)
    tx_hash = w3.eth.send_raw_transaction(signed.rawTransaction)
    return tx_hash.hex()
```

Variables de entorno: `GAIA_CHAIN_RPC`, `CARBON_CREDIT_CONTRACT_ADDRESS`, `PRIVATE_KEY`.

---

## Alertas en Grafana / Prometheus

Reglas en `kubernetes/prometheus/alert-rules-carbon.yaml`:

- **HighCarbonSavings:** cuando `carbon_credits_total > 1000` (1 tonelada CO₂) durante 1h, severidad info.

Exponer la métrica `carbon_credits_total` desde el backend (ej: endpoint `/metrics` o exportador Prometheus) con label `region`.

---

[ArgoCD Multi-Cluster](argocd-multi-cluster.md) · [Deploy](deploy.md)
