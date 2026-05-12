# Integración Stripe — Pagos Recurrentes y Facturación

**Objetivo**: Licencias y certificaciones con pagos recurrentes. Reducción del **40%** en tiempo de facturación.

---

## Uso

- **Suscripciones**: Planes Basic/Pro/Enterprise (tiered pricing).
- **Pagos únicos**: Certificaciones express, paquetes puntuales.
- **Facturación**: Stripe Invoicing o integración con Zoho Books para facturas automáticas.

---

## Webhooks

- `invoice.paid`, `customer.subscription.updated`, `payment_intent.succeeded`.
- Endpoints ya referenciados en el proyecto (ej. `/webhooks`); validar firma Stripe-Signature.

---

## Métrica de éxito

- **-40%** tiempo dedicado a facturación manual.
- Renovaciones y cobros recurrentes automatizados.
