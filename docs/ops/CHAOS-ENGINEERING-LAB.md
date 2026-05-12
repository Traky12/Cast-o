# Chaos engineering — laboratorio CASTÚO (medición honesta)

**Qué es:** herramientas y un webhook n8n opcional para **ensayos controlados** de disponibilidad y **estimación de RTO** mediante sondas HTTP. **No** sustituyen un plan de HA con proxy + standby ni pruebas de restauración de Postgres.

**Qué no hace el repo hoy:** conmutación automática entre instancias n8n al caer un “núcleo”. Ver [failover-strategy.md](failover-strategy.md).

---

## Definir “núcleo”

En este laboratorio, un **núcleo** es una entrada en `CASTUO_CHAOS_TARGETS` (JSON): `id` + `url` que debe responder (p. ej. health de cada contenedor, gateway, o endpoint de otro host). No implica que existan 313 procesos reales hasta que tú los listes en el fichero.

---

## Componentes

| Artefacto | Rol |
|-----------|-----|
| `scripts/chaos/castuo_chaos_lab.py` | `probe`, `drill-sample`, `recovery` (medición RTO), `report` (Markdown) |
| `n8n/workflows/castuo-chaos-lab-report-ingest.json` | Ingesta opcional del informe vía `POST .../webhook/chaos-lab-report` |

---

## Fichero de objetivos (ejemplo)

Plantilla en repo: `scripts/chaos/targets.example.json`. Copia y ajusta URLs reales (health dedicado si existe).

Guarda p. ej. `config/chaos/targets.json` (ruta libre; no versiones secretos):

```json
[
  { "id": "n8n-castuo", "url": "http://localhost:5678/healthz", "method": "GET", "expect_status": 200 },
  { "id": "backend-api", "url": "http://localhost:8000/health", "method": "GET", "expect_status": 200 }
]
```

Ajusta paths reales (`/healthz` depende de la imagen n8n; muchos usan raíz o métricas). Si no hay health dedicado, documenta el riesgo de medir “200 genérico” sin semántica.

---

## Guion de ensayo (operador)

1. **Línea base:** `python scripts/chaos/castuo_chaos_lab.py probe --targets-file config/chaos/targets.json --out artifacts/chaos/probe-before.json`
2. **Muestra de caída (50 aleatorios):** `python scripts/chaos/castuo_chaos_lab.py drill-sample --targets-file config/chaos/targets.json --count 50 --seed 42` → lista de `id` para pausar o aislar **manualmente** (`docker pause`, firewall, stop de réplica, etc.). El script **no** tumba servicios por ti.
3. **Inyectar fallo:** actúa sobre la infraestructura según tu runbook (no automatizado aquí).
4. **Medir recuperación:** `python scripts/chaos/castuo_chaos_lab.py recovery --targets-file config/chaos/targets.json --interval 2 --max-wait 900 --out artifacts/chaos/recovery.json`  
   - RTO (estimado en este ensayo) = tiempo desde el inicio del comando hasta la primera iteración donde **todos** los objetivos devuelven `expect_status`.
5. **Informe:** `python scripts/chaos/castuo_chaos_lab.py report --probe artifacts/chaos/probe-before.json --recovery artifacts/chaos/recovery.json --out artifacts/chaos/resilience_run.md`
6. **Opcional n8n:** con el workflow importado, `POST` el JSON del informe a `/webhook/chaos-lab-report` para trazabilidad en flujo (Trillizo/Slack lo cableas después).

---

## Verificación de “failover automático”

Solo puedes marcar ✅ *failover automático* si tienes **comprobación objetiva**: p. ej. proxy que enruta a upstream B cuando A falla, con **misma** URL pública y prueba repetible. El comando `recovery` mide **vuelta al verde** de la lista; si tras el fallo sigues apuntando al mismo upstream caído, el RTO refleja **reparación manual**, no conmutación.

---

## Relación con narrativa comercial

Incluye en el informe: fecha, entorno (staging/prod), responsable, lista de `id` muestreados en el drill y **método** de inyección. Evita claims genéricos sin pegar el `recovery.json` o el Markdown generado.
