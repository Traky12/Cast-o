# CastuoRegistry — integración Web3

## Contrato

`contracts/CastuoRegistry.sol` — `submitEvidence(bytes32, string dataRoomId)` emite `EvidenceSubmitted`.

## ABI

`contracts/CastuoRegistryABI.json`

## Python (web3)

```python
from web3 import Web3
import json
w3 = Web3(Web3.HTTPProvider(os.environ["RPC_URL"]))
abi = json.load(open("contracts/CastuoRegistryABI.json"))
c = w3.eth.contract(address=w3.to_checksum_address(os.environ["REGISTRY_ADDR"]), abi=abi)
tx = c.functions.submitEvidence(evidence_bytes32, "DR-2026-042").build_transaction({...})
```

## Flujo previo

1. `scripts/sign_evidencehash_hsm_generic.sh` → hash + `.sig`
2. Subir `dataRoomId` (IPFS/WORM pointer)
3. `submitEvidence` on-chain
