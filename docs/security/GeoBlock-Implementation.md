# Implementación Geobloqueo — Barreras Sabionda v6.1

**Objetivo**: Bloquear IPs de Rusia, China, Corea del Norte, Irán. Excepciones para CTAEX, GlobalGAP, AEMPS.

---

## Opciones

1. **Cloudflare WAF**: Reglas por país (block RU, CN, KP, IR); whitelist por IP o ASN para CTAEX, GlobalGAP, AEMPS.
2. **Nginx**: `geo $block_country { default 0; RU 1; CN 1; KP 1; IR 1; }` + `if ($block_country) { return 403; }`; excepciones con `geo $allow_ip { ... }`.
3. **Backend (FastAPI)**: Middleware que resuelve IP → país (MaxMind GeoIP2 o similar) y rechaza con 403 salvo whitelist.

---

## Whitelist (IP / ASN)

- OVH ENS Madrid (principal).
- n8n cloud (automatización).
- Hetzner CAX21 (backup).
- AWS Frankfurt (UE), Google Cloud (USA), Azure West Europe.
- Rangos CTAEX, GlobalGAP, AEMPS (listas proporcionadas por cada parte).

---

## Métricas

- Tasa de bloqueo de IPs maliciosas o de países bloqueados: >99 %.
- Sin bloqueos indebidos de whitelist (monitorear 403 en IPs conocidas).
