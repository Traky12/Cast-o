# CUMPLIMIENTO POR PAÍS / REGIÓN (plantilla operativa)

Este documento sirve como checklist mínimo por jurisdicción. Ajustar con asesoría local cuando aplique.

---

## Unión Europea (GDPR + marcos UE)

- Base legal: consentimiento explícito para datos personales en talleres.
- Minimización: evitar recoger email/identificadores si no es necesario.
- Seguridad: cifrado en reposo y en tránsito cuando haya servicios online.
- Derechos: acceso/rectificación/supresión/portabilidad.

Acciones en repo:

- Plantillas: `docs/legal/POLITICA-PRIVACIDAD.md`, `docs/legal/TERMINOS-Y-CONDICIONES.md`
- Cifrado local: `scripts/seguridad/encriptar_aes_gcm.py`
- Auditoría: `scripts/revision/`

---

## México (LFPDPPP)

- Aviso de privacidad en español.
- Consentimiento informado.
- Recomendación: almacenamiento local para pilotos educativos.

Acciones:

- Añadir “Aviso de privacidad (MX)” (sección) en `POLITICA-PRIVACIDAD.md`.

---

## España (LOPDGDD + GDPR)

- Registro interno de actividades de tratamiento (si se opera servicio online).
- Contacto de privacidad / DPO (si aplica).

Acciones:

- `PLACEHOLDER: definir correo de privacidad y proceso de solicitudes`

---

## Estados Unidos (COPPA/CCPA) — si se opera con menores

- Evitar recogida de datos de menores sin mecanismos apropiados.
- Transparencia de datos recogidos y opt-out.

Acciones:

- Operar talleres en modo offline sin cuentas.

