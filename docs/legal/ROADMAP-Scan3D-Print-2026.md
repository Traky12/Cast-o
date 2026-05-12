# Roadmap Scan3D → impresión (orientativo) — Castúo 2026

**En repo:** simulación **TRL-4** bajo `POST /api/robotics/lab/scan3d/*` en el **robotics lab stub** (`lab_stub_app`). **No** incluye triangulación láser real, ni slicer, ni envío de GCode binario a máquina.

**Sellado:** firma **Dilithium** (vía `pq_crypto`) sobre JSON de auditoría del paso (`chain_seal`). **No** es transacción on-chain hasta que se integre `register_event_in_chain` con política acordada.

---

## Flujo honesto

1. **Escaneo** (campo): nube de puntos / malla en estación de trabajo o firmware del escáner.  
2. **Lab API** (`/scan`): devuelve métricas **simuladas** coherentes con `points` / tamaño de subida (no valida PLY/STL).  
3. **Slicing** (campo): Bambu Studio, PrusaSlicer, Cura, etc.  
4. **Impresión**: OctoPrint, Bambu Connect, u OEM; **API key y red aislada** si expones OctoPrint.  
5. **Trazabilidad opcional**: sellado Dilithium en respuesta; anclaje on-chain con `register_event_in_chain` si `CASTUO_ROBOTICS_LAB_CHAIN_REGISTER=1` y variables `GAIA_*` válidas → `on_chain_tx_hash` en `POST .../print` (ver DPIA robótica).

---

## Hardware (referencia comercial, no presupuesto contractual)

| Rol | Ejemplos de mercado | Notas |
|-----|---------------------|--------|
| Escaneo 3D | Equipos metrología / escáner estructurado luz | Precisión y software dependen del modelo; verificar licencias de exportación si aplica. |
| FDM | Impresoras cartesianas / CoreXY de fabricante estable | Volumen útil y materiales según datasheet. |
| SLA | Resinas y post-procesado químico | Residuos y REACH local. |
| Orquestación | OctoPrint, Klipper, stacks propietarios | No exponer sin TLS + auth fuerte. |

**Precios:** consultar distribuidor; no usar este documento como oferta.

---

## Variables de entorno

| Variable | Uso |
|----------|-----|
| `CASTUO_PRINT_MAX_BUILD_MM` | Tope de bbox simulada (default 256). |

---

## Relación

- [ROADMAP-Robotics-2026.md](./ROADMAP-Robotics-2026.md)  
- [ROADMAP-Neuromorphic-2026.md](./ROADMAP-Neuromorphic-2026.md) (`apply_neuro_hints` en `/print`)  
- [DPIA-Robotics-2026.md](./DPIA-Robotics-2026.md) si se almacenan mallas ligadas a persona/parcela identificable.

---

*El territorio valida el prototipo; el stub solo ordena el ritual de datos.*
