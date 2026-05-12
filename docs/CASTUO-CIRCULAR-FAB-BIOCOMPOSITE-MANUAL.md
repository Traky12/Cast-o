# Fase producción local — Circular FAB (cáñamo + FDM)

Manual para taller rural: biocomposites, impresión 3D y trazabilidad hacia gemelo digital.

## 1. Biocomposite Castuo (carenados no críticos)

| Fase | Material |
|------|----------|
| Matriz | PLA industrial o **PETG reciclado** |
| Refuerzo | Fibra corta **cáñamo** local |
| Propiedad | Aislamiento térmico natural frente a entorno caliente (electrónica) |

## 2. Impresión FDM (gran formato)

**Piezas:** carenados ventilación PEM, soportes sensores, anclajes plug-and-play (**±0,1 mm** sellado).

| Parámetro | Valor |
|-----------|--------|
| Boquilla | 230–245 °C |
| Infill | **40 % gyroid** |
| Post | Resina epoxi **ignífuga** (criterio aeronáutico local) |

## 3. Módulo rescate — camilla eléctrica (<10 min)

1. Desacople depósito **~2200 L** (4 pernos quick-release).
2. Bus **CAN** camilla ↔ IA embarcada.
3. Fijación camilla carbono/cáñamo al chasis.
4. Test alimentación **Li-Ion respaldo** → soporte vital.

## 4. QC y legalidad local — Protocolo Trazabilidad Castuo

1. **Escaneo 3D** post-impresión vs CAD.
2. **Carga 1,5×** operativa.
3. **Registro blockchain:** ID único → lote + fecha inspección en **gemelo digital** del dron (coherencia con capa consenso [CASTUO-ECOSYSTEM-6X](CASTUO-ECOSYSTEM-6X-ARQUITECTURA.md)).
