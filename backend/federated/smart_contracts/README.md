# Smart Contracts — CASTÚO Federated v3.0

Contratos Solidity para **smart_gdpr** (agente CONTRACTS): registro de consentimientos GDPR on-chain.

- **GDPRConsent.sol**: registro y revocación de consent (hash) por dirección. Emisión de eventos para auditoría.
- Despliegue opcional en **Ethereum Sepolia** para trazabilidad Stage 2.

## Uso

```bash
# Compilar (Solidity 0.8.x)
solc --bin --abi GDPRConsent.sol -o build/
# Desplegar con Hardhat/Foundry a Sepolia
```

El agente **contracts** en `agent_federation.py` puede llamar a `recordConsent(consentHash)` vía RPC (SEPOLIA_RPC).
