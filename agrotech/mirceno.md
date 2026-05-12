# Mirceno en contexto agrotech

Este documento describe el uso de perfilado de mirceno en CASTUO-SYSTEM para operaciones de cultivo controlado.

## Objetivo operativo

- Mantener un perfil de referencia de beta-mirceno para lotes de laboratorio.
- Relacionar variables ambientales (`humedad`, `ph`, `ec`, `luz_umol`, `uvb_ratio`) con estabilidad de perfil terpénico.
- Integrar trazabilidad en flujos n8n y auditoría técnica.

Marco ético y de trazabilidad (obligatorio para despliegues): `agrotech/ETHICS_TRACEABILITY.md`.

## Perfil orientativo de cultivo

- Rango de referencia: `0.1-0.5%` en peso seco (objetivo de laboratorio, no garantía).
- Condiciones sugeridas:
  - `luz_umol`: `800-1200`
  - `temp`: `24-28C`
  - `ph`: `5.8-6.2`
  - `ec`: `1.0-1.6`

## Integración con inferencia neuromórfica

Endpoint recomendado para pruebas:

- `POST /api/robotics/lab/neuromorphic/hydroponics/infer`

Payload de ejemplo:

```json
{
  "humedad": 65,
  "ph": 5.8,
  "ec": 1.2,
  "luz_umol": 1000,
  "target_terpene": "mirceno"
}
```

## Fuentes botánicas no cannabis (referenciales)

- Mirceno: mango maduro, tomillo, lúpulo, laurel.
- Limoneno: cáscaras de limón, naranja, mandarina, pomelo.
- Pineno: romero, salvia, coníferas.

## Cumplimiento y límites

- Este contenido es técnico-agronómico y de trazabilidad.
- No constituye consejo médico ni sustituto de evaluación clínica.
- Cualquier declaración terapéutica comercial debe validarse con marco regulatorio aplicable y asesoría jurídica.

## Protección de datos y minimización (RGPD / eIDAS contexto operativo)

- Tratar solo datos necesarios para el cultivo y la trazabilidad del lote; evitar datos personales en webhooks y alertas (Telegram) salvo base legal y registro en el tratamiento.
- Referencia de soberanía y marco legal del repositorio: `docs/legal/MARCO-LEGAL-SOBERANIA-UE-2026.md`.

