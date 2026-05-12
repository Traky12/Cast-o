# Conectividad TRL10 (UE): Sateliot · núcleo 5G open source · Arsys

**Estado:** borrador de arquitectura — **validar** con documentación oficial de cada proveedor antes de producción.  
**Versión doc:** 0.2.1  
**Alineación:** CASTÚO-SYSTEM (hidroponía / trazabilidad); actualizar [DPIA](../legal/DPIA-CASTUO-SYSTEM.md) y registro de actividades si se tratan datos personales vía estas vías.

---

## 1. Objetivo

Diseñar una **cadena opcional** de conectividad para sensores y telemetría:

1. **Acceso NTN / IoT** (p. ej. ecosistema tipo **Sateliot** — 5G IoT / NTN): publicación MQTT hacia un broker controlado por CASTÚO o híbrido.
2. **Núcleo 5G** open source (referencia **NextEPC** u homologable **3GPP**): laboratorio o edge soberano; **no** sustituye el acuerdo contractual con un MNO sin integración real.
3. **Nube / conector** con proveedor **español** (p. ej. **Arsys**): backup, IoT platform o colas — siempre con **DPA** y localización acordada.

---

## 2. Diagrama lógico (texto)

```text
Sensores / nodo edge (CASTÚO)
        │  MQTT/TLS (configurable)
        ▼
Broker MQTT (propio / Sateliot / mixto) ──► Backend CASTÚO / GaiaChain / almacén
        │
        └──► (opcional) Core 5G lab (NextEPC u open5gs) — solo si hay proyecto radio validado
        │
        └──► (opcional) Arsys IoT / almacenamiento — DPA + cifrado en tránsito
```

---

## 2.1 Modo GEMelo-céntrico (SoT lógico)

Cuando el **gemelo digital** actúa como **punto único de verdad** para telemetría NTN:

```text
Sateliot / broker NTN  ──►  Ingest GEMelo (HTTP)  ◄──  audit / cifrado de sobre
                               │
                               └──►  CASTÚO  (solo pull por `gemelo_id`)
```

- **Unidireccional hacia CASTÚO:** los sensores no publican “directo” al core de negocio; el consumo es **GET** (o equivalente) por identificador global devuelto por el gemelo.
- **IDs:** exponer **`gemelo_id`** (o alias acordado) como correlación; evitar reutilizar IDs de sensor crudos como clave de sistema.
- **Resiliencia:** si el servicio GEMelo no está disponible, la cadena NTN → CASTÚO queda **sin SoT**; definir cola edge o degradación acordada (no asumida aquí).
- **Artefactos:** `scripts/sateliot_gemelo_bridge.py`, `scripts/gemelo-centric.yml`.

El modo **MQTT directo** (`sateliot_bridge.py`) sigue siendo válido para laboratorios o acuerdos donde el broker ya cumple rol de frontera.

---

## 3. Variables de entorno (no commitear valores)

| Variable | Uso |
|----------|-----|
| `SATELIOT_MQTT_HOST` | Host broker acordado con Sateliot (o broker intermedio). |
| `SATELIOT_MQTT_PORT` | Puerto (1883 sin TLS solo en lab; **8883** + TLS en prod). |
| `SATELIOT_MQTT_USER` / `SATELIOT_MQTT_PASSWORD` | Credenciales (secret store). |
| `SATELIOT_MQTT_TOPIC` | Tema raíz (p. ej. `castuo/sensors/{finca}`). |
| `ARSYS_MQTT_HOST` / … | Análogo para segundo salto o ingest Arsys. |
| `CASTUO_SENSOR_JSON` | Cuerpo JSON de una lectura (o fichero vía stdin en scripts). |
| `GEMELO_BASE_URL` | Base URL del servicio gemelo (p. ej. `http://gemelo-digital:8001`). |
| `GEMELO_INGEST_PATH` | Ruta POST ingest (defecto `/agents/gemelo/ingest`). |
| `GEMELO_CASTUO_PATH_TEMPLATE` | Plantilla GET pull; `{gemelo_id}` sustituido por el id. |
| `GEMELO_ENVELOPE_SECRET` | Secreto opcional para HMAC del sobre de ingest (recomendado fuera de lab). |
| `CASTUO_NTN_SOURCE` | Etiqueta de origen (defecto `sateliot_sband`). |

---

## 4. Artefactos en el repo

| Artefacto | Ruta |
|-----------|------|
| Bridge MQTT → broker configurado | `scripts/sateliot_bridge.py` |
| Gateway NTN → GEMelo → CASTÚO (HTTP, pull) | `scripts/sateliot_gemelo_bridge.py` |
| Bridge / reenvío hacia segundo broker (plantilla) | `scripts/arsys_bridge.py` |
| Plantilla Compose núcleo 5G (validar imágenes) | `docker/nextepc-compose.template.yml` |
| Compose GEMelo-céntrico (imágenes a validar) | `scripts/gemelo-centric.yml` |

---

## 5. Cumplimiento (marco)

- **GDPR:** DPIA si hay datos personales o localizaciones identificables; minimización en payloads.
- **NIS2 / ciberseguridad UE:** inventario de proveedores críticos, contratos y registro de incidentes.
- **ETSI / 3GPP:** aplicable al despliegue **real** de core y RAN; esta plantilla **no** certifica conformidad.

---

## 6. Checklist antes de TRL10 productivo

- [ ] Contrato / anexo técnico con Sateliot (o MNO) con topics, QoS y TLS.
- [ ] Broker con autenticación fuerte; rotación de claves.
- [ ] Imágenes Docker del core 5G contrastadas con el proyecto open source elegido.
- [ ] DPA con Arsys (o proveedor equivalente) y cláusulas de subencargado si aplica.
- [ ] DPIA y Registro de actividades actualizados.
- [ ] (Modo GEMelo) Contrato OpenAPI o equivalente para `/ingest` y `/castuo`; TLS mutuo si aplica; `GEMELO_ENVELOPE_SECRET` en almacén de secretos.
- [ ] (Modo GEMelo) Imagen `castuo/gemelo-digital` construida o sustituida; volumen cifrado en reposo según política.

---

## 7. Smoke test local (`sateliot_gemelo_bridge`)

Requiere un servicio en `GEMELO_BASE_URL` que implemente el **POST** de ingest (respuesta con `gemelo_id`) y el **GET** de vista CASTÚO. Sustituye `<gemelo_id>` por el valor impreso en el paso *ingest*.

### Bash

```bash
export GEMELO_BASE_URL=http://localhost:8001
export CASTUO_SENSOR_JSON='{"sensor":"ph","value":7.2}'
python scripts/sateliot_gemelo_bridge.py ingest
python scripts/sateliot_gemelo_bridge.py pull "<gemelo_id>"
```

### PowerShell (Windows)

```powershell
$env:GEMELO_BASE_URL = "http://127.0.0.1:8001"
$env:CASTUO_SENSOR_JSON = '{"sensor":"ph","value":7.2}'
python scripts/sateliot_gemelo_bridge.py ingest
python scripts/sateliot_gemelo_bridge.py pull "<gemelo_id>"
```

### Git — ejemplo TRL10.1 (handoff)

Si ya existe el primer commit en historial, el segundo añade solo GEMelo; si **no** hay commits previos, conviene **un único** `git add` + `commit` con todo el conjunto para no duplicar archivos.

**Opción A — un solo commit (recomendado si empiezas desde cero):**

```bash
git add docs/PRONTUARIO_MAESTRO_ESCALADO_TRL9_TRL13.md docs/legal/DPIA-CASTUO-SYSTEM.md \
  docs/legal/TRL10/README_WINDOWS.md scripts/arsys_bridge.py scripts/sateliot_gemelo_bridge.py \
  scripts/gemelo-centric.yml docs/architecture/TRL10-CONEC-EU-SATELIOT-NEXTEPC-ARSYS.md
git commit -m "TRL10.1: handoff UE + GEMelo-céntrico (Prontuario v1.2.1)

- §17.3 conectividad UE + modo GEMelo
- DPIA §4.1 encargados NTN/5G/IoT
- README_WINDOWS v1.2.1; bridges y compose"
git push
```

**Opción B — dos commits (handoff escalonado):**

```bash
git add docs/PRONTUARIO_MAESTRO_ESCALADO_TRL9_TRL13.md docs/legal/DPIA-CASTUO-SYSTEM.md \
  docs/legal/TRL10/README_WINDOWS.md scripts/arsys_bridge.py
git commit -m "TRL10.1: handoff cerrado (Prontuario v1.2.1 + DPIA + bridges UE)
- §17.3 Conectividad UE (Sateliot/NextEPC/Arsys)
- DPIA §4.1 Encargados NTN/5G
- README_WINDOWS v1.2.1 + arsys_bridge.py v1.2.1"
git push

git add scripts/sateliot_gemelo_bridge.py scripts/gemelo-centric.yml \
  docs/architecture/TRL10-CONEC-EU-SATELIOT-NEXTEPC-ARSYS.md \
  docs/PRONTUARIO_MAESTRO_ESCALADO_TRL9_TRL13.md docs/legal/DPIA-CASTUO-SYSTEM.md \
  docs/legal/TRL10/README_WINDOWS.md
git commit -m "TRL10.1 GEMelo-céntrico operativo (v1.2.1)
- sateliot_gemelo_bridge.py (urllib + HMAC + CLI)
- gemelo-centric.yml (--profile fiveg)
- Prontuario §17.3 + docs arquitectura v0.2.1"
git push
```

*(En el segundo commit de la opción B, los docs solo entran si tienen cambios nuevos respecto al primer commit.)*

---

## 8. Referencias (consulta obligatoria en implementación)

- Documentación oficial **Sateliot** (conectividad, MQTT, seguridad).
- Repositorio y guías del **núcleo 5G** elegido (NextEPC / open5gs / otro).
- Portal **Arsys** (API IoT, RGPD).

*Este documento no es oferta comercial de terceros; describe integración técnica propuesta para CASTÚO-SYSTEM.*
