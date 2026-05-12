# Implementación HSM — Thales / AWS CloudHSM

**Objetivo**: 100 % de claves críticas almacenadas en HSM. Alineado con Prompt-Guide v4.1 (corto plazo 2026).

---

## Alcance

- Claves de firma GaiaChain (cuenta de registro).
- Secretos de API (AEMPS, GlobalGAP, CTAEX).
- Claves de cifrado para datos sensibles en reposo (opcional).

---

## Pasos

1. **Selección**: Thales Luna o AWS CloudHSM según infraestructura.
2. **Contratación e instalación**: Según proveedor (3 meses orientativo).
3. **Migración gradual**: Primero GaiaChain y API keys; luego cifrado de BD si aplica.
4. **Rotación**: Procedimiento documentado de rotación anual y recuperación.

---

## Referencias

- [Guía HSM](HSM-Guide.md)
- [PSI ISO 27001](../validation/security/PSI-ISO27001.md)
