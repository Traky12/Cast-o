# CASTO 1.0 → ECO-STEALTH 5.0 — Ruta tecnológica

**Parte 1:** optimización del prototipo actual para que sea **funcional y seguro hoy**.  
**Parte 2:** hoja de ruta hacia concepto **ECO-STEALTH 5.0** (visión 2030).

---

## PARTE 1 — Optimización CASTO 1.0 (actual)

### Propulsión y energía

| Actual | Mejora | Motivo |
|--------|--------|--------|
| A2212 | **2216 / 2312 (900 KV)** | Más par para láser + disipadores sin sobrecalentar. |
| 3S 3000 mAh 25C | **4S 4500 mAh 50C** | Evitar voltage sag al activar láser; comprobar ESC y controladora 4S. |

### Blindaje térmico

- **Chasis F450** (ABS/fibra): ablandamiento ~80–90 °C.
- **Escudo:** cinta aluminio/Kapton bajo chasis y brazos cerca motores.
- **Separadores:** sustituir nylon por **aluminio/acero** en placa láser (nylon funde con calor).

### Seguridad óptica

- **Interlock:** canal RC (p. ej. Arduino Nano) como “armado” del láser: **solo dispara** si dron armado **y** interruptor físico en emisora activo.
- **Próximo paso crítico:** esquema **Arduino Nano + controladora F4** para **failsafe** — apagado automático del láser si se pierde señal de radio (evitar incendios/accidentes ópticos).

---

## PARTE 2 — Evolución ECO-STEALTH 5.0 (2030)

### Estructura

| Actual | Objetivo |
|--------|----------|
| ABS / fibra de vidrio | **Bio-metaestructura:** fibra cáñamo + nanotubos de carbono; geometría fractal para dispersión radar. |
| RCS tipo “águila” | RCS tipo “insecto” (~−55 dB). |

### Térmica

- **Enfriamiento pasivo:** pintura termocrómica/cerámica; microcanales de grafeno hacia puntas de hélices (máximo flujo).

### Energía

- **Perovskita** en brazos → carga en vuelo.
- **Piezo:** vibraciones motor → micro-corriente para sensórica de seguridad.

### Seguridad

- **IA fotónica/cuántica:** auto-bloqueo láser (evolución del interlock físico).

---

## Comparativa

| Característica | CASTO 1.0 | ECO-STEALTH 5.0 |
|----------------|-----------|------------------|
| Material | ABS / fibra de vidrio | Bio-metamaterial cáñamo/grafeno |
| Firma radar | Alta (km) | Casi nula (−55 dB) |
| Resistencia calor | ~80 °C | ~1 550 °C (pico cerámico) |
| Autonomía | 12–15 min | Objetivo ilimitada (RF/solar) |
| Seguridad láser | Manual / visual + interlock | IA fotónica (auto-bloqueo) |

---

*Siguiente hito recomendado:* diseño del esquema de conexión **Arduino Nano ↔ F4** para failsafe del láser ante pérdida de señal RC.
