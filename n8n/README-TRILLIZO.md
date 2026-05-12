# Trillizo digital (quinta instancia n8n)

## Rol en arquitectura

La instancia **`n8n-trillizo`** es un contenedor n8n **aparte** (volumen y `N8N_ENCRYPTION_KEY` opcionalmente distinta vía `N8N_TRILLIZO_ENCRYPTION_KEY`) pensado para:

- Workflows de **auditoría**, correlación cruzada y alertas de seguridad.
- Webhooks internos que **no** deben compartir cola con sensores en tiempo real.

No sustituye un gemelo físico ni ejecuta ZKP reales por sí sola: es **el lugar del lienzo** donde implementas reglas (HTTP a satélite, histórico, listas de veto, etc.).

## Qué queda fuera de este repo (y dónde hacerlo)

| Capa prometida en diseño | Implementación verificable |
|---------------------------|----------------------------|
| mTLS entre contenedores | Red Docker bridge **no** cifra tráfico entre servicios. mTLS: **proxy inverso** (nginx, Traefik), **service mesh**, o TLS terminado en cada servicio. |
| Cifrado en reposo AES-256 | **Volumen/host**: LUKS, cifrado de disco del proveedor, o DB gestionada cifrada. No es un flag de Compose. |
| ZKP / ancla GaiaChain cada 10 min | Integración explícita (nodos HTTP, contratos, servicio ZK). Plantilla de workflow + `GAIACHAIN_*` en `.env`. |
| “Quórum / veto” automático | Patrón: Trillizo responde **veto/allow** y el workflow de actuación **solo continúa** si el Trillizo lo permite (rama IF o subworkflow). El gateway actual **reenvía**; no veta solo. |

## Compose

Servicio **`n8n-trillizo`** en `docker-compose.multi-n8n.yml` (puerto host **5682** por defecto, límite de memoria **2G** vía `deploy.resources`; en entornos sin Swarm, Compose puede ignorar `deploy` según versión).

Variable de rol solo informativa para tus Code nodes: **`CASTUO_TRILLIZO_ROLE=shadow_validator`**.

## Gateway

Rutas añadidas en `castuo_main_orchestrator_gateway.json`:

- `trillizo/audit-rotation` → `POST …/webhook/audit-rotation` en `N8N_WEBHOOK_BASE_TRILLIZO`
- `trillizo/shadow-check` → `POST …/webhook/shadow-check`

Crea esos webhooks en el lienzo del Trillizo o ajusta paths en el gateway.

## Scripts

- `scripts/n8n/trillizo_audit_notify.sh` — notificación segura a un webhook del Trillizo (sin tocar claves).
- `scripts/n8n/rotar_bunker.sh` — **no** rota `N8N_ENCRYPTION_KEY` automáticamente (rompería credenciales sin el flujo oficial de n8n); imprime advertencia y enlaces.

## Referencia n8n sobre clave de cifrado

Cambiar `N8N_ENCRYPTION_KEY` requiere el procedimiento soportado por tu versión de n8n (export, migración, backup). Consulta la documentación actual en https://docs.n8n.io/hosting/
