# BioPay-Quality-v1 — pago cooperativa por Pe (potencial etanólico)

## Actores

| Rol | Función |
|-----|---------|
| **Productor** | Cooperativa; recibe pago. |
| **Oráculo IoT** | NIR en tolva: % azúcares, humedad. |
| **Contrato** | Calcula Pe y ejecuta pago desde tesorería. |
| **Tesorería** | ETH en contrato (`depositTreasury`). |

## Fórmula (on-chain)

Pe ∝ **M** × **%Azúcares** × **(1 − %Humedad)** × **(1 + Bonus)**  
`Bonus` = huella carbono negativa (drones monitoreo), en basis points.

- Humedad **&gt;25 %** → revert (`MAX_MOISTURE_BPS`).
- Grado emitido en evento: A+ Premium / A / B.

## Contrato

`contracts/BioPayQualityV1.sol`

1. `registerShipment(id, producer, weightKg)` — oráculo.
2. `submitQualityAndPay(id, sugarBps, moistureBps, carbonBonusBps)` — oráculo.
3. Admin: `setOracle`, `setBasePrice`.

## Flujo JIT (transparencia)

1. Falcon X: parcela lista cosecha.  
2. Blockchain: orden transporte.  
3. Recepción: IoT → oráculo → **&lt;5 s** pago (sin factura manual / 90 días).

## Estandarización sensores

Schema NIR recepción alineado con `tools/manifest_template.json` y API planta (próximo endpoint `/v1/biopay/oracle-submit`).
