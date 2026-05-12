# Manual de Subvenciones — ForestOwnershipToken

Cálculo y documentación de subvenciones (PAC 2040, Decreto 45/2020, Red Natura 2000).

---

## 1. Cálculo on-chain

El contrato `ForestOwnershipToken` expone:

- **calculateSubsidies(tokenId)** → total en €/año.
- **getEligibleSubsidies(tokenId)** → códigos (p. ej. `PAC_2040:200`, `Decreto_45_2020:150`).

## 2. Uso desde CLI

```bash
# Total en €/año
python3 backend/scripts/calculate_subsidies_forest.py 1

# Detalle de códigos y certificaciones
python3 backend/scripts/calculate_subsidies_forest.py 1 -v
```

## 3. Reglas de subvención (implementadas en contrato)

| Código | Condición | Importe (€/ha/año) |
|--------|-----------|---------------------|
| PAC_2040 | Siempre (por área) | 200 |
| Decreto_45_2020 | Certificación PEFC o FSC | 150 |
| Red_Natura_2000 | Certificación "Red Natura 2000" | 300 |
| Area_Protegida | isProtected y sin Red Natura | 100 |

## 4. Reclamación efectiva

La reclamación de subvenciones (mint de SubsidyToken o pago vía administración) se realiza fuera del contrato ForestOwnershipToken; este contrato solo calcula la elegibilidad y el importe. Para integración con SubsidyToken, ver documentación del contrato de subvenciones.

---

*Versión PDF: exportar desde este Markdown.*
