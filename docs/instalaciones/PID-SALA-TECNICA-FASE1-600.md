# P&ID — Sala técnica: agua, ozono y control (Fase 1 → 600 m²)

Corazón hídrico de los **100 m² iniciales**, predimensionado para **600 m²**.

## 1. Purificación (entrada red)

| Etapa | Detalle |
|-------|---------|
| Filtrado primario | Malla **130 µm** — sólidos en suspensión |
| Descalcificación | Resinas si dureza local **> 15 °fH** (protección membranas) |
| Ósmosis inversa | **~1,5 m³/h**; rechazo a depósito secundario (limpieza / recuperación) |
| Pulmón | **2 000 L** agua osmotizada **< 40 µS/cm** (20–40 µS/cm banda operativa) |

## 2. Activación y mezcla (ozono + nutrientes)

- **Bucle recirculación:** bomba → **Venturi** → inyección O₃.
- **Generador ozono:** **30–40 g/h**; tanque contacto **5–8 min** (patógenos superficiales).
- **ORP:** setpoint **650–750 mV** en contacto.
- **Destructor O₃:** catalítico salida aire — sala técnica sin fugas de gas.
- **Fertirrigación:** Venturi / peristálticas — soluciones A/B + ácido **tras** ozonización.

## 3. Distribución y retorno

- **Colector anillo PEAD Ø63 mm** — presión homogénea hacia **10 alturas**.
- **Electroválvulas zona** — PLC, ciclos **ebb & flow**.
- **Retorno 1 % pendiente** → depósito muestreo; IA ajusta receta según lixiviado.

## Prioridades cuadro eléctrico (Fase 1)

| Componente | Potencia | Control | Prioridad |
|------------|----------|---------|-----------|
| Bomba impulsión riego | ~1,5 kW | VFD | Crítica |
| Planta OI | ~2,2 kW | PLC | Media |
| Generador O₃ | ~0,8 kW | ORP | Crítica |
| PLC + sensores | ~0,1 kW | UPS / batería | Vital |

## Fail-safe (alineado AGRI-SENSE)

- **pH fuera 5,5–6,5:** cierre electroválvula maestra + alerta IA.
- **O₃ ambiental:** paro generador + extractores **100 %**.
- **Bombas:** protección marcha en seco (caudal).
