# MotionEye ↔ CASTÚO-SYSTEM (integración avanzada)

**Objetivo:** dashboard CASTÚO (SSE ~3 s) + MotionEye (EU OSS) + borde endurecido (Qubes/Whonix en estación de trabajo, no en este compose).

```
CASTÚO Dashboard SSE  ←→  MotionEye (RTSP/MJPEG en UI propia)  ←→  IoT / cámaras
   métricas JSON            snapshot vía proxy autenticado
```

## 1. Por qué no hay “SSE proxy de vídeo”

Los eventos **Server-Sent Events** son texto UTF-8. Inyectar **MJPEG binario** en el mismo `text/event-stream` **rompe** el protocolo y el `EventSource` del navegador.

Patrón CASTÚO:

| Canal | Contenido |
|--------|-----------|
| `GET /agents/camera/stream` | SSE `event: camera_update` — solo JSON (`online`, `latency_ms`, `health`, …) |
| `GET /agents/camera/snapshot/{id}` o `/frame/latest` | Imagen JPEG proxy (Basic Auth en servidor) |

La UI MotionEye sigue en `:8765`; el dashboard embebe **snapshot** refrescado.

## 2. Despliegue MotionEye

```powershell
copy .env.camera.example .env.camera
# editar MEYE_* / CASTUO_MOTIONEYE_* según entorno

.\scripts\Deploy-MotionEye.ps1
```

Compose: `docker-compose.camera.yml` (red `castuo-net`, volúmenes bajo `data/motioneye` por defecto).

**Seguridad:** no commitear contraseñas; firewall/UFW según política (exponer 8765 solo a VPN o reverse proxy TLS).

## 3. Variables del backend FastAPI

| Variable | Ejemplo |
|----------|---------|
| `CASTUO_MOTIONEYE_BASE` | `http://127.0.0.1:8765` (host) o `http://motioneye:8765` (misma red Docker) |
| `CASTUO_MOTIONEYE_USER` | usuario UI MotionEye |
| `CASTUO_MOTIONEYE_PASSWORD` | secreto (solo entorno / secret manager) |
| `CASTUO_CAMERA_SSE_INTERVAL` | `3` (segundos entre eventos SSE) |

## 4. Endpoints

- `GET /agents/camera/stream` — SSE `camera_update`
- `GET /agents/camera/snapshot/1` — JPEG cámara 1
- `GET /agents/camera/frame/latest?camera_id=1` — alias para plantillas

## 5. Trazabilidad

```powershell
.\scripts\Register-SecurityEvent.ps1 `
  -EventType "motioneye_integrated" `
  -EventData @{ source = "EU_OpenSource"; compose = "docker-compose.camera.yml" }
```

(`Register-SecurityEvent.ps1` exige `-EventData`; no usar `-Metadata` a menos que el script lo defina.)

## 6. Legal / expediente

- IoT y vídeo pueden activar **DPIA** y bases jurídicas (CTAEX anexos); alinear con `docs/legal/DPIA-CASTUO-SYSTEM.md`.
- Retención de frames/logs: política explícita; no asumir “0 exposición” sin pentest y hardening de red.

## 7. Demo CTAEX (flujo)

1. `uvicorn backend.main:app --host 0.0.0.0 --port 8000` (o el puerto acordado)
2. `http://localhost:8000/dashboard` — SSE métricas + bloque cámara
3. MotionEye UI: `http://<host>:8765` para configuración RTSP

## 8. KPIs (orientativos)

| Métrica | Notas |
|---------|--------|
| Cámaras gestionadas | Por instancia MotionEye |
| Dashboard SSE | CPU/Mem + `camera_update` |
| Superficie de ataque | Cerrar 8765/8081/554 a Internet; TLS delante |

---

**Prontuario maestro:** [PRONTUARIO-MAESTRO-CASTUO-SYSTEM-2040.md](../PRONTUARIO-MAESTRO-CASTUO-SYSTEM-2040.md)
