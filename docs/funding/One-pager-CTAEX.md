# One-pager CASTÚO 360 S.L. — CTAEX / Fundecyt / PAC 2040

**Empresa:** CASTÚO 360 S.L. (Extremadura, España)  
**Contacto:** Gregorio J Jiménez Bodes (Fundador/CTO)  
**Fecha:** Marzo 2026

---

## Problema

Cooperativas agrovoltaicas necesitan **trazabilidad inmutable** (campo → informe), cumplimiento **GDPR/AI Act/PAC 2040** y herramientas de **IA** para optimización de riego, energía y certificación.

## Solución

**CASTÚO-SYSTEM™**: plataforma SaaS que integra:

- **Motor IA (Mistral):** análisis de datos agrícolas, recomendaciones, informes de cumplimiento.
- **API Cooperativas:** parcelas, socios, elegibilidad PAC 2040, ROI estimado.
- **GaiaChain 2.0:** registro de hashes/trazas para auditoría y subvenciones.
- **IoT + MQTT:** sensores (ph, ec, temp) y bandejas Sabionda en tiempo real.

## Arquitectura (1 diagrama)

```
Cooperativa → Frontend/API → Mistral Adapter → Mistral API
                ↓                    ↓
           Backend (8001)      GaiaChain (witness)
                ↓
           /cooperativas, /pac2040/eligibilidad, /metrics
```

## TRL y hitos

| TRL | Estado | Hito |
|-----|--------|------|
| 6   | ✅     | Componentes validados (Mistral, cooperativas MVP, GaiaChain witness) |
| 7   | 🎯     | Demo sistema completo en entorno real (Sabionda Educa + 1 cooperativa) |

## Métricas actuales (referencia)

| Métrica | Valor |
|---------|--------|
| Cooperativas activas (MVP) | 3 |
| Total kWp (paneles) | 9.500 |
| PAC 2040 elegible | €360K |
| Financiación actual | 605K€ (JEREMIE) |
| Proyección revenue | 125M€ |
| ROI objetivo 2026 | 100% |

*Fuente: `/metrics` y `/compliance` de la API.*

## Ask

- **Subvención PAC 2040:** criterios 14.2.1 Agrovoltaica, 6.1 Jóvenes agricultores (ver [PAC2040-Criterios.md](PAC2040-Criterios.md)).
- **CTAEX / Fundecyt:** apoyo a piloto Sabionda Educa y despliegue en cooperativas Extremadura.

---

*Documento vivo; actualizar con datos reales de producción.*
