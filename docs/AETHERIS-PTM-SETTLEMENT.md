# Liquidación PTM — EnergyCredit + API

## Smart Contract: `contracts/EnergyCredit.sol`

| Concepto | Implementación |
|----------|----------------|
| **DID / HSM** | Identidad nodo = hash off-chain vinculado a HSM; on-chain `sourceIdHash` / `targetIdHash`. |
| **PoT** | Receptor + emisor firman (`submitPoT`); `settle` exige ambos ack. |
| **Tarifa dinámica** | `tariffWeiPerKwh` fijada por **settler** (Castuo Cloud 5.X) según demanda y solar. |
| **Eficiencia óptica** | ~**85 %** en monto liquidado (ajustable en `openSession`). |

Depositar ETH en contrato antes de `settle`.

## API FastAPI

`POST /v1/aetheris/ptm/session` — cuerpo JSON:

```json
{
  "source_node_id": "URN:CASTUO:AETHERIS:...",
  "target_node_id": "URN:CASTUO:AETHERIS:...",
  "energy_kwh": 2.5,
  "laser_frequency_thz": 194.0
}
```

Respuesta mock incluye `tx_hash`; sustituir por llamada Fabric/Web3.

## Handshake operativo

1. **Emergency_Beacon** (batería &lt;20 %) vía Ultra-Link.
2. **Matchmaking** IA: nodo cercano &gt;80 % + línea de visión.
3. **Alineación gimbal** (gemelo compensa viento/vibración).
4. **Haz IR** + sensores corriente.
5. **Smart contract** `EnergyCreditSettled` → billetera cooperativa.

## Seguridad láser

- **Corte &lt;1 ms** si objeto cruza LOV (ave / aeronave).
- Pérdidas: modelar óptica vs eléctrica en LCA energético.

## Recompensas

- Incentivo nodos en altitud / exposición solar superior (tarifa dinámica).

Ver [AETHERIS-ULTRA-LINK-PROTOCOL.md](protocolos/AETHERIS-ULTRA-LINK-PROTOCOL.md), [BioPayQualityV1.sol](../contracts/BioPayQualityV1.sol) (pagos biomasa).
