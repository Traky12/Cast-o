# Protocolo de Tala Legal — Actualización de CO₂

Flujos para actualizar el CO₂ secuestrado tras talas (Orden 15/03/2021, Ley 3/2023).

---

## 1. Normativa

- **Orden 15/03/2021:** Gestión de montes públicos y planificación forestal.
- **Ley 3/2023 de Montes:** Registro y trazabilidad de aprovechamientos.

## 2. Actualización on-chain

Solo el propietario del token puede actualizar el CO₂. Fórmula utilizada:

- Reducción = `volume_m3 × 1000` kg CO₂ (1 m³ madera ≈ 1 t CO₂ equivalente).
- Nuevo valor = `carbonSequestered - reducción` (mínimo 0).

## 3. Uso del script

```bash
# Actualizar tras tala de 10 m³ en la parcela del token 1
python3 backend/scripts/update_carbon_after_cutting.py 1 10
```

Requisitos: `FOREST_OWNERSHIP_TOKEN_ADDRESS` y `PRIVATE_KEY` (cuenta propietaria del token).

## 4. Flujo recomendado

1. Obtener permiso de tala (PublicForestToken / GreenLicenseToken según procedimiento Junta).
2. Ejecutar la tala y registrar volumen.
3. Llamar a `update_carbon_after_cutting.py` con el token de propiedad y el volumen en m³.
4. Opcional: emitir CarbonCredit por la madera vendida (módulo aparte).

---

*Versión PDF: exportar desde este Markdown.*
