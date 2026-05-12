# Castuo 360 — Limpieza industrial en altura (láser tethered)

Ver evolución **CASTO LÁSER v2.1** (TiAlC, IA federada, CASTO-QC): [CASTUO-LASER-v2.1-ARQUITECTURA.md](CASTUO-LASER-v2.1-ARQUITECTURA.md).

## Umbilical híbrido

- **600–800 VDC** a ~30 m (láser **500–2000 W**): menor sección conductor (**~1,0 mm²**), menos peso y drag.
- **Winch par constante:** catenaria controlada — ni tensión excesiva (pérdida maniobrabilidad) ni flojo (riesgo rotor X8).

## Refrigeración

- Láser **~1 kW óptico** → **2–3 kW** calor residual típico.
- **Agua-glicol** en micro-mangueras (umbilical) + **placa fría microcanales** en cabezal → estabilidad **λ ≈ 1064 nm**.

## Plataforma X8 coaxial

- Redundancia motor; empuje para vencer arrastre umbilical en barrido.
- **Fibra en umbilical:** inmunidad EMI del láser.
- **LiPo 12S backup:** **3–5 min** descenso seguro si cae enlace energía.

## Seguridad láser

- **Interlock distancia** (LiDAR/US): bloqueo si **> 50 cm** o **< 10 cm** de superficie.
- **EN 60825-1 Clase 4:** cortinas / vallado exclusión.

## Cadena de valor España (soberanía)

| Capa | Actor | Notas |
|------|-------|-------|
| Estructura / compuestos | **ATyges** (Málaga) | Plataformas alta carga |
| Control vuelo | **Embention** (Alicante) | Veronte, SORA |
| Potencia HVDC | **Ingeteam** (País Vasco) | Conversión industrial |

*Próximo hito crítico: chiller en base + gimbal amortiguando vibraciones bomba refrigeración.*
