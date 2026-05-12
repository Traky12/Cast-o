# Roadmap CASTUO Nano/Lab — Entregables para inversores y reguladores

Tres líneas de trabajo para **materializar** la arquitectura ya definida. Pueden ejecutarse en paralelo con equipos distintos.

---

## A) Protocolo de enjambre (Swarm)

**Objetivo:** **10× CASTUO Nano** mapean una mina (o galería) en **~5 min** con cobertura y redundancia.

| Tema | Contenido entregable |
|------|----------------------|
| Topología | Mesh local (UWB / Wi-Fi 6E confinado) + relé a estación móvil |
| SLAM federado | Mapas parciales → fusión sin centralizar nube (edge) |
| Seguridad | Líder elegible; acuerdo de altura/velocidad; aborto en cascada XAI |
| Salida | Especificación protocolo + diagrama secuencia + riesgos SORA |

*Próximo paso código:* módulo simulación multi-agente (opcional repo `sim/swarm_nano`).

---

## B) Cuadro de mandos — estación móvil (AR/VR)

**Objetivo:** Interfaz para **misiones críticas**: teleoperación brazo háptico, SLAM compartido, logs XAI en panel.

| Capa | Entregable |
|------|------------|
| UX | Wireframes misión: Nano (mapa 3D) + Lab (espectro + brazo) |
| AR | Overlay peligros químicos / vectores viento sobre video downlink |
| VR | Brazo háptico con límites fuerza por tipo muestra |
| Auditoría | Stream firmado hacia CASTUO Ledger (ver Nano/Lab doc) |

---

## C) Simulación «Patrimonio en riesgo» ✅ detallada

**Operación [«Cripta del Silencio»](CASTUO-SIMULACION-OPERACION-CRIPTA-SILENCIO.md):** 3× Nano en fila, US + SLAM, Lab VOC/háptico, informe CASTO-QC, **API logs XAI** [API-XAI-LEDGER-LOGS.md](API-XAI-LEDGER-LOGS.md) + código `backend/patrimonio/xai_ledger.py`.

| Fase | Actuación |
|------|-----------|
| 1 | Nano: SLAM + LiDAR densidad baja humedad; mapa geométrico cripta |
| 2 | Detección patologías (hongo, sales) → hint para muestreo háptico |
| 3 | Lab: MS portátil aire + muestra sólida; informe con **EvidenceHash** tipo CASTO-QC |
| 4 | Entrega | Informe PDF + ancla ledger + anexo conservación |

Útil para **CNMC cultura**, seguros, y alineación [CASTO LÁSER v2.1](CASTUO-LASER-v2.1-ARQUITECTURA.md).

---

## Recomendación de secuencia

1. **C** demuestra narrativa única (patrimonio + ciencia) en dossier regulatorio.  
2. **A** escala operativa minas/túneles.  
3. **B** cierra el bucle humano-máquina para contratos defensa/infraestructura.

*Prioridad final: acordar con socio CTAEX / licitación objetivo.*
