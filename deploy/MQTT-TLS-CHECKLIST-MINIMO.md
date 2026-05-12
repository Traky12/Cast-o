# Checklist mínimo — MQTT TLS (priorizado)

Objetivo: broker Mosquitto con TLS en VPS (p. ej. Hetzner) alineado con agua CASTÚO y n8n. Rutas relativas a la **raíz del repositorio** salvo donde se indique `cd deploy`.

---

## 1. Implementación inmediata (bloqueante)

### 1.1. Archivos y acciones

| Archivo | Acción |
|---------|--------|
| `deploy/docker-compose.mqtt.yml` | Desplegar desde el directorio `deploy/` (ver §1.2) |
| `deploy/mqtt-tls/scripts/gen-certs.sh` | Ejecutar con `MQTT_CN=mqtt.tu-dominio.com` |
| `deploy/mqtt-tls/scripts/init-passwd.sh` | Copiar desde `init-passwd.example.sh`, exportar variables, ejecutar |

### 1.2. Comandos (orden)

```bash
cd /ruta/al/repo/Castuo-System

chmod +x deploy/mqtt-tls/scripts/gen-certs.sh
MQTT_CN=mqtt.tu-dominio.com ./deploy/mqtt-tls/scripts/gen-certs.sh

cp deploy/mqtt-tls/scripts/init-passwd.example.sh deploy/mqtt-tls/scripts/init-passwd.sh
chmod +x deploy/mqtt-tls/scripts/init-passwd.sh
# Exportar CASTUO_MQTT_ADMIN_PASS, CASTUO_MQTT_ORP_PASS, … (cabecera del script)
./deploy/mqtt-tls/scripts/init-passwd.sh

cd deploy
docker compose -f docker-compose.mqtt.yml up -d
docker logs mosquitto-tls
```

Desde la raíz del repo (alternativa):

```bash
docker compose -f deploy/docker-compose.mqtt.yml --project-directory deploy up -d
```

### 1.3. Conectividad TLS (validación)

```bash
mosquitto_pub -h mqtt.tu-dominio.com -p 8883 \
  -t "castuo/water/sensor/orp" -m "620" \
  --cafile deploy/mqtt-tls/mosquitto/certs/ca.crt \
  -u sensor_orp -P 'tu_contraseña_orp' \
  --tls-version tlsv1.2
```

API (misma máquina que castuo-api):

```bash
curl -s "http://127.0.0.1:8000/water/ctaex/health"
```

**n8n:** el mensaje MQTT no llama solo a la API; hace falta el workflow activo y credencial MQTT (`mqtts://`, puerto 8883, usuario `n8n_system`, CA). Comprueba ejecuciones en la UI de n8n.

---

## 2. Firewall (Hetzner / UFW)

```bash
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow 8883/tcp
sudo ufw deny 1883/tcp
sudo ufw enable
sudo ufw status
```

Ajusta reglas si 1883 solo existe en `127.0.0.1` del host (el `deny` entrante sigue siendo buena práctica en borde público).

---

## 3. Verificación extremo a extremo

### 3.1. Publicar ORP crítico (580 mV)

```bash
mosquitto_pub -h mqtt.tu-dominio.com -p 8883 \
  -t "castuo/water/sensor/orp" -m "580" \
  --cafile deploy/mqtt-tls/mosquitto/certs/ca.crt \
  -u sensor_orp -P 'tu_contraseña_orp' \
  --tls-version tlsv1.2
```

### 3.2. API análisis (esperado `analysis.status`: `critical`)

```bash
curl -s -X POST "http://127.0.0.1:8000/water/ctaex/analyze" \
  -H "Content-Type: application/json" \
  -d '{"sensor_type": "orp", "sensor_value": 580}'
```

### 3.3. Logs del broker

```bash
docker logs mosquitto-tls
# o en tiempo real:
docker logs -f mosquitto-tls
```

### 3.4. Métricas `$SYS` (requiere usuario con permiso, p. ej. `admin`)

```bash
mosquitto_sub -h 127.0.0.1 -p 8883 \
  -t '$SYS/broker/load/#' \
  --cafile deploy/mqtt-tls/mosquitto/certs/ca.crt \
  -u admin -P 'tu_contraseña_admin' \
  --tls-version tlsv1.2
```

En el servidor, `127.0.0.1:8883` debe ser alcanzable desde el host donde ejecutas el cliente.

---

## 4. Referencia rápida

### 4.1. Topics y usuarios ACL

| Topic | QoS recomendado | Descripción | Usuario típico |
|-------|-----------------|-------------|----------------|
| `castuo/water/sensor/orp` | 1 | ORP (mV) | `sensor_orp` |
| `castuo/water/sensor/tds` | 1 | TDS (ppm) | `sensor_tds` |
| `castuo/water/sensor/ph` | 1 | pH | `sensor_ph` |
| `castuo/water/actuator/ozone` | 1 | Ozono | `actuator_ozone` |
| `castuo/water/actuator/osmosis` | 1 | Ósmosis | `actuator_osmosis` |

### 4.2. Umbrales API agua (proyecto)

| Parámetro | Crítico | Advertencia | Óptimo |
|-----------|---------|-------------|--------|
| ORP | &lt; 600 mV | &lt; 650 mV | 650–750 mV |
| TDS | &gt; 50 ppm | &gt; 40 ppm | &lt; 40 ppm |
| pH | &lt; 5.5 o &gt; 6.5 | &lt; 5.8 o &gt; 6.2 | 5.8–6.2 |

### 4.3. Emergencia / operación

| Situación | Comando |
|-----------|---------|
| Reiniciar broker | `cd deploy && docker compose -f docker-compose.mqtt.yml restart` |
| Logs en vivo | `docker logs -f mosquitto-tls` |
| Clientes conectados (aprox.) | `mosquitto_sub -h 127.0.0.1 -p 8883 -t '$SYS/broker/clients/connected' -C 1 -u admin -P '…' --cafile deploy/mqtt-tls/mosquitto/certs/ca.crt` |
| Backup certs | `tar czvf mqtt-certs-backup-$(date +%Y%m%d).tar.gz -C deploy mqtt-tls/mosquitto/certs` |

La imagen oficial `eclipse-mosquitto` no incluye por defecto `mosquitto_ctrl` con *dynamic-security* como en despliegues con plugin aparte; usa logs, `$SYS` o métricas externas.

---

## 5. Estado del proyecto (orientativo)

| Componente | Notas |
|------------|--------|
| Workflow n8n agua | `n8n/workflows/castuo_n8n_water_mqtt_analysis.json` — activar y credenciales MQTT TLS |
| API `/water/ctaex/analyze` | Implementada en castuo-api |
| MQTT TLS | Pendiente hasta ejecutar §1 en el servidor |
| Firewall | Pendiente según política del VPS |
| Backups Postgres / Keycloak / Slack / runbooks | Revisar en **tu** entorno real; no asumir hechos sin verificación |

---

## 6. Compose en la raíz del repo

Si existe `docker-compose.mqtt.yml` en la raíz, delega en `deploy/docker-compose.mqtt.yml` para una sola fuente de verdad.

Documentación ampliada: `deploy/mqtt-tls/README.md`.
