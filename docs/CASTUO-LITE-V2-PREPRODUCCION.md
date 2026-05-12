# CASTUO LITE V2.0 — Pre-producción (autonomía, térmica láser, RFI, paracaídas)

## 1. Autonomía dinámica (peor escenario)

Factor combinado **η_total ≈ 0,63** (BMS, viento, envejecimiento celdas):

$$t_{vuelo} = \frac{E_{nom} \cdot \eta_{total}}{P_{hover} + P_{laser}}$$

| Config | Batería | MTOW | P_total | Tiempo safe* |
|--------|---------|------|---------|--------------|
| P1A MVP | LiPo 6S 16 Ah | 9,2 kg | 985 W | ~13,6 min |
| P1B Pro | Li-ion 7S 21 Ah | 11,4 kg | 1120 W | ~19,2 min |

\*Incluye **~20 %** reserva RTH.

## 2. Térmica láser 100 W — PWM 4 niveles

| T | Acción |
|---|--------|
| < 40 °C | Ventilador 0 % |
| 40–55 °C | 30 % (laminar) |
| 55–65 °C | 100 % boost |
| > 70 °C | **Cutoff MOSFET** láser + FC aterrizaje emergencia |

## 3. Eléctrico y RFI (RTK)

- Mástil carbono **60 mm** para GNSS, alejado de EMI motores.
- **Motores AWG 10** (picos ~80 A); aviónica **AWG 22** + **DC-DC galvánicos**.
- Telemetría **900 MHz** separada **>150 mm** de antena GPS (desensibilizado).

## 4. Paracaídas balístico (P1B)

- Eyección muelle/CO₂ si **roll/pitch > ~80°** o pérdida potencia total.
- **P1A:** tethered controlado, sin paracaídas.
- **P1B:** **2,5 m²**, V_impacto **< 5 m/s** objetivo.

**Certificación:** alineación AESA/SORA con documentación láser en [CASTUO-LASER-v2.1-ARQUITECTURA.md](CASTUO-LASER-v2.1-ARQUITECTURA.md).
