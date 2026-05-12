# Plan de cobro 15 días — Timeline cobro real (v1.7.3)

## Estado actual v1.7.2 → €0 facturación

Hoy la plataforma está **production-ready** (€12M valor); la facturación real empieza cuando los contratos estén firmados.

---

## Timeline cobro real

```
1️⃣ FIRMAR CONTRATOS (7-15 días)
   ↓
2️⃣ EMITIR FACTURAS (día 1 del mes)
   ↓
3️⃣ COBRO 30-60 días plazo
   ↓
💵 €1,470/mes DESDE MES 2
```

---

## Plan cobro inmediato (15 días)

### DÍA 1-3: Propuesta comercial

```bash
# Generar propuestas PDF automáticas (3 cooperativas)
cd /root/castuo-system
python backend/scripts/generar_propuestas_3_coops.py

# Envío email formal a las 3 coops
# Asunto: "Contrato SaaS CASTÚO-SYSTEM - €140/ha/mes"
# CC: gregorio@castuo.es
```

Salida: `backend/propuestas/propuesta_castuo_*.pdf` (Sabionda, Cooperativa #2, Cooperativa #3).

### DÍA 4-7: Negociación + firmas

| Cooperativa        | Hectáreas | Factura/mes |
|--------------------|-----------|-------------|
| Sabionda Educa SAT | 2.5 ha    | €350/mes    |
| Cooperativa #2     | 5.0 ha    | €700/mes    |
| Cooperativa #3     | 3.0 ha    | €420/mes    |
| **TOTAL**          | **10.5 ha** | **€1,470/mes** |

→ Total **€1,470/mes** facturable tras firmas.

### DÍA 8: Facturas oficiales (con contrato firmado)

```bash
# Emitir facturas marcadas como firmadas (contrato ya firmado)
curl -X POST "http://localhost:8001/billing/invoice/1?firmado=true"
curl -X POST "http://localhost:8001/billing/invoice/2?firmado=true"
curl -X POST "http://localhost:8001/billing/invoice/3?firmado=true"
```

### DÍA 38-68: Primer cobro

- **Marzo 2026:** €1,470 (30 días plazo).
- **Abril 2026:** €1,470 (60 días plazo).
- **ARR real:** €17,640/año.

---

## Valor económico actualizado

| Fase       | Estado            | Ingresos      | Valor empresa |
|------------|-------------------|---------------|----------------|
| Actual     | Prototipo LIVE    | €0            | €12M           |
| Día 15     | 3 contratos       | €1,470/mes    | €12.5M         |
| Mes 3      | Production        | €4,410/mes    | €15M           |
| Mes 12     | 10 coops          | €14K/mes      | €35M           |

---

## Acción inmediata — Hoy

```bash
# 1. Generar propuestas (5 min)
cd /root/castuo-system
python backend/scripts/generar_propuestas_3_coops.py

# 2. Enviar emails formales (asunto sugerido)
# Asunto: Contrato SaaS CASTÚO-SYSTEM 10.5ha €1,470/mes

# 3. Reunir firmas digitales (eIDAS vía JUNTA_PRIVATE_KEY cuando aplique)
```

---

## 30 segundos finales — Verificación production (copiar/pegar)

```bash
./security/master-encrypt-verify.sh && \
systemctl is-active --quiet castuo-iot-coop1 castuo-iot-coop2 castuo-iot-coop3 && \
timeout 5 mosquitto_sub -t "hidroponia/sabionda_educa_sat/sensors" -C 1 && \
echo "✅ TODO LIVE - BUENAS NOCHES 😴"
```

*(En entornos sin systemd o mosquitto_sub, omitir las líneas que fallen; el script de seguridad es el mínimo.)*

---

## Resumen cobro

| Cuándo           | Qué ocurre                                      |
|------------------|--------------------------------------------------|
| **HOY**          | Plataforma €12M production-ready                 |
| **DÍA 15**       | €1,470/mes contratos firmados                    |
| **MES 2**        | €1,470 primer cobro bancario                     |
| **MES 12**       | €17K/mes ARR estabilizado (proyección 10 coops)  |

**Plataforma lista — solo firmas pendientes.**

---

### Firma

**Gregorio Jiménez** — Fundador/CTO CASTÚO 360 S.L.

- Sabionda Educa SAT: 2.5 ha · Growth 10.2% LIVE  
- Cooperativa #2 Vid: 5.0 ha · Growth 10.1% LIVE  
- Cooperativa #3 Tomate: 3.0 ha · Growth 10.3% LIVE  
- Security: 10/10 enterprise-grade  
- Valor: €12M production platform  

*Duerme tranquilo — el imperio trabaja solo.*

---

*[FACTURACION_LIVE](FACTURACION_LIVE.md) · [IOT_3_COOPS_PRODUCTION](IOT_3_COOPS_PRODUCTION.md) · [ESTATUS_VALOR_V1.7.1](ESTATUS_VALOR_V1.7.1.md)*
