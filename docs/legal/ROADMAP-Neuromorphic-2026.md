# Roadmap neuromórfico y materiales (orientativo) — Castúo 2026

**Estado en repo:** simulación **TRL-4** en `backend/integrations/robotics/neuromorphic_edge.py` + endpoint en el **robotics lab stub**. **No** implica presencia de silicio Loihi2, NeuRRAM ni wafers de laboratorio en el despliegue Castúo.

**Concepto ampliado (tabla, Mermaid, materiales, métricas):** [NEUROMORPHIC-MEMRISTOR-ORIENTACION-2026.md](../integrations/NEUROMORPHIC-MEMRISTOR-ORIENTACION-2026.md)

**Materiales (literatura técnica):** perovskitas haluro doble sin plomo (p. ej. **Cs₂AgBiBr₆**) y capas buffer se investigan para dispositivos de memoria/resistencia; **cualquier uso agro** exige validación ambiental, encapsulado y normativa de residuos — este documento **no** es hoja de datos de fabricación.

---

## Hitos sugeridos (no compromiso contractual)

| ID | Descripción | En clon hoy | Próximo paso honesto |
|----|-------------|-------------|----------------------|
| NM-001 | Inferencia hidropónica simulada (SNN + STDP toy) | `HydroponicsSNN`, `POST .../hydroponics/infer` | Sustituir por modelo calibrado con datos CTAEX / sensores reales |
| NM-002 | Fusión sensorial edge | Metadatos en `signal_manager` si `CASTUO_NEUROMORPHIC_LAB=1` | Contrato JSON estable + DPIA si hay PII |
| NM-003 | Trazabilidad | `dilithium_sign` sobre payload canónico | Anclar a `register_event_in_chain` cuando política de gas/token lo permita |

---

## Variables de entorno (lab)

| Variable | Uso |
|----------|-----|
| `CASTUO_ECO_ALLOY` | Etiqueta de aleación en metadatos (default `Cs2AgBiBr6`) |
| `CASTUO_NEUROMORPHIC_LAB` | `1` → enriquece `log_snapshot` con `neuromorphic_inference` cuando hay `humedad`/`ph`/`ec` en metadata |

---

## Mercado y cifras

Las estimaciones de mercado global y CAGR **no** se fijan aquí como hechos auditables; usar informes sectoriales y citas verificables en documentación comercial aparte.

---

## Relación legal

- [DPIA-Robotics-2026.md](./DPIA-Robotics-2026.md) si se graban operadores o entornos identificables.  
- [ROADMAP-Robotics-2026.md](./ROADMAP-Robotics-2026.md) para alcance del lab HTTP.

---

*Documento orientativo; el territorio y el agua priman sobre el benchmark.*
