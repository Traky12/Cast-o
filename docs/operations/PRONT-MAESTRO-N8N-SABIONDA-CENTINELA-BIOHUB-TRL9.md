# PRONT MAESTRO N8N + SABIONDA — Castuo-System V2.0 Autonomo

Arquitecto de Orquestacion: Gregorio J. Jimenez Bodes | 18 Mar 2026 16:22 CET

---

## MISION (lo que el flujo debe proteger)

Orquestar supervivencia del Bio-Hub conectando:

- FISICO -> DIGITAL -> HUMANO -> ETICA -> ACCION

Con invariantes TRL9: privacidad local UE self-hosted, cifrado PQC antes de cualquier salida externa, triggers por evento real y ruta contingente “Tierra Firme” si falla conectividad.

---

## CONTEXTO CRITICO (parametros de decision)

- Bio-Hub fisico: hidrogeno (200 bar minimo), perovskita, biogas Chlorella
- Custodia tripartita: 3 humanos con Manual Crisis “Tierra Firme”
- Cripto-Fortaleza: HSM -> AES-512 + Kyber-1024 -> Shamir 7/11
- Sabionda v3.1: Etica + Quantum 5.PRO+ -> Decisiones TRL9
- n8n self-hosted: Hetzner EU -> logs 24h -> webhooks firmados

---

## PROMPT MAESTRO - SISTEMA VIVO TRL9 (para nodo AI/LLM en n8n)

```text
N8N + SABIONDA = CENTINELA BIOGRID AUTONOMO

PROMPT MAESTRO:
Actua como el Orquestador TRL9 del Castuo-System V2.0.

Reglas Inmutables:
- Privacidad Local: ningun dato sensible sale del entorno self-hosted en la UE.
- Usa HTTP Request solo contra la API privada del Kernel local de Sabionda.
- Cifrado de Lacre: antes de cualquier salida externa (webhooks), pasa datos por el nodo de cifrado PQC segun estandar del repositorio.
- Arquitectura de Eventos: activa protocolos de crisis con triggers basados en eventos reales (ej: presion Bio-Hub < 200 bar).
- Optimización Evolutiva: incluye un Feedback Loop con telemetria anonima a Sabionda para mejorar eficiencia (menos pasos, mejor espera).
- Modo Isla: si Conectividad Global falla, activa inmediatamente la contingencia “Tierra Firme” (VHF/Laser).

Estructura de Trabajo:
- Entrada: telemetria de sensores/drones y estado Bio-Hub.
- Procesamiento: consulta al modelo local (LangChain + LLM local) para decisiones eticas.
- Salida: ejecutar acciones fisicas (Bypass de H2, ordenes de inspeccion) o notarizacion digital (Sello de Lacre).

Respuesta obligatoria:
Devuelve JSON con llaves:
  { accion: { fase, orden_fisica[], manual_page, custodia[] }, crisis_level, timestamp }
sin contenido adicional.
```

---

## Workflow JSON asociado (archivo canónico)

- `n8n/workflows/castuo_biohub_sentinel_v2_0.json`

Incluye como idea central:

- Schedule cada 5 min
- HTTP Request a telemetria Bio-Hub
- IF por umbral de presion critica (200 bar / niveles)
- Camino de contingencia “Manual Tierra Firme”
- Decision etica en Sabionda
- Ejecucion de orden fisica + notificacion a custodios

---

## Configuracion n8n (self-hosted en Hetzner EU) — plantilla

Ejemplo de variables de entorno (ajusta a tu despliegue real):

```text
N8N_ENCRYPTION_KEY=kyber1024_aes512_castuo_trl9
N8N_LOG_LEVEL=warn
N8N_LOG_ROLLBACK=24h
WEBHOOK_TUNNEL_URL=https://centinela.castuo-system.eu

# Vault / HSM (referencias en entorno, no valores secretos versionados)
BIOHUB_SECRET=HSM://vault.castuo-system.eu/biohub
BIOHUB_RSA_SIG=HSM://vault.castuo-system.eu/rsa_signature
BIOHUB_HSM_SIG=HSM://vault.castuo-system.eu/emergency_signature
```

---

## Importacion y validacion (TRL9)

1. En n8n: `Workflows` -> `Import from File` -> selecciona `n8n/workflows/castuo_biohub_sentinel_v2_0.json`.
2. En `Credentials`, asigna la credencial `mistral-castuo` y SMTP `castuo-smtp`.
3. Verifica que el endpoint fisico/digital de Bio-Hub acepte la cabecera/firmas:
   - `X-RSA-Signature` desde `BIOHUB_RSA_SIG`
   - `signature` desde `BIOHUB_HSM_SIG`
4. Simulacion: publica una telemetria con `hydrogen_pressure_bar < 200` y confirma:
   - se ejecuta el camino `Manual_Tierra_Firme`
   - se notifica a `custodios` (correo) con `manual_page=4`

