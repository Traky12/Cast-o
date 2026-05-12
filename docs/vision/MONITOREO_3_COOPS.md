# Monitoreo real-time — 3 cooperativas IoT LIVE (v1.7.3)

Sensores EC/pH/DO/Temp + NFT Growth de Sabionda Educa SAT, Cooperativa #2 y Cooperativa #3.

---

## Alcance: terminal local → multi-capa enterprise

| Antes | Ahora |
|-------|--------|
| 📡 Terminal local | 📡 **Multi-capa enterprise** |

```
├── Terminal:   dashboard_3_coops.sh (CLI)
├── Web API:    localhost:8001/alertas (JSON)
├── Logs:       backend/logs/alertas.log (Audit)
├── Email:      gregorio@castuo.es (Móvil)
└── MQTT:       hidroponia/+/sensors (Estándar)
```

### Todo en 1 línea (copiar/pegar)

```bash
./scripts/dashboard_3_coops.sh & sleep 3; curl -s localhost:8001/alertas | jq .alertas_activas; tail -2 backend/logs/alertas.log
```

*(Dashboard en segundo plano + cuenta de alertas activas + últimas 2 líneas del log.)*

---

## Dashboard terminal — real-time

### Opción 1: Watch (cada 5s)

Ejecutar en pestaña separada:

```bash
watch -n 5 '
echo "=== DASHBOARD 3 COOPERATIVAS ===" && \
echo "🟢 Cooperativas: $(curl -s localhost:8001/cooperativas | jq length)/3" && \
echo "💎 NFT Status:" && \
echo "  #1 $(curl -s localhost:8001/nft/status/1 | jq -r ".growth // 0")%" && \
echo "  #2 $(curl -s localhost:8001/nft/status/2 | jq -r ".growth // 0")%" && \
echo "  #3 $(curl -s localhost:8001/nft/status/3 | jq -r ".growth // 0")%" && \
echo "💰 Facturación: €$(curl -s localhost:8001/billing/facturacion | jq \"[.[].total_eur] | add // 0\")" && \
echo "🔒 Security: $(./security/master-encrypt-verify.sh 2>/dev/null | head -1)"
'
```

### Opción 2: Super dashboard (script, cada 10s)

```bash
chmod +x scripts/dashboard_3_coops.sh
./scripts/dashboard_3_coops.sh
```

Ctrl+C para salir.

### Ejemplo de salida

```
🚜 CASTÚO-SYSTEM v1.7.3 - 2026-03-16 04:42 CET
═══════════════════════════════════════════════════════
🏭 COOPERATIVAS: 3/3
📈 SUPERFICIE:   10.5 ha
💎 NFT GROWTH:
  Sabionda #1:  10%
  Coop #2:      10%
  Coop #3:      10%
💰 FACTURACIÓN:  €1470
🔒 SECURITY:     CASTÚO-SYSTEM ENCRYPTION: 10/10 SECURE
📡 MQTT:         broker activo

Actualizando cada 10s (Ctrl+C salir)
```

---

## MQTT — sensores 3 cooperativas

Topics publicados por los IoT monitors (EC, pH, DO, temp, growth):

| Terminal | Cooperativa        | Topic MQTT                                  |
|----------|--------------------|---------------------------------------------|
| 1        | Sabionda Educa SAT | `hidroponia/sabionda_educa_sat/sensors`     |
| 2        | Coop #2 Vid        | `hidroponia/cooperativa_2/sensors`          |
| 3        | Coop #3 Tomate     | `hidroponia/cooperativa_3/sensors`          |
| 4        | Todas (wildcard)   | `hidroponia/+/sensors`                      |

Comandos (sustituir `localhost` por el host del broker si aplica):

```bash
# Terminal 1: Sabionda Educa SAT (2.5 ha)
mosquitto_sub -h localhost -t "hidroponia/sabionda_educa_sat/sensors" -v

# Terminal 2: Coop #2 Vid (5.0 ha)
mosquitto_sub -h localhost -t "hidroponia/cooperativa_2/sensors" -v

# Terminal 3: Coop #3 Tomate (3.0 ha)
mosquitto_sub -h localhost -t "hidroponia/cooperativa_3/sensors" -v

# Terminal 4: Todas (wildcard)
mosquitto_sub -h localhost -t "hidroponia/+/sensors" -v
```

---

## Dashboard web — localhost:3000

| URL                    | Contenido                          |
|------------------------|------------------------------------|
| http://localhost:3000  | Dashboard principal, cooperativas  |
| http://localhost:3000/privacidad  | Módulo GDPR (derecho al olvido) |
| http://localhost:3000/facturacion  | Facturación €1,470/mes LIVE       |

**Facturación mes actual (ejemplo):**

| Cooperativa     | Hectáreas | Importe | Estado   |
|-----------------|-----------|---------|----------|
| Coop #1 Sabionda| 2.5 ha    | €350    | PENDIENTE|
| Coop #2 Vid     | 5.0 ha    | €700    | PENDIENTE|
| Coop #3 Tomate  | 3.0 ha    | €420    | PENDIENTE|
| **Total**       | **10.5 ha** | **€1,470** |          |

---

## API — datos raw

```bash
# 1. Cooperativas (10.5 ha total)
curl -s localhost:8001/cooperativas | jq '[.[].parcelas[].hectares] | add'

# 2. NFT growth (token 1, 2, 3)
curl -s localhost:8001/nft/status/1 | jq
# → {"token_id":1,"growth":10.2,"last_update":"...","status":"LIVE"}

# 3. Facturación (último mes)
curl -s localhost:8001/billing/facturacion | jq 'map({coop: .coop_id, total: .total_eur})'

# 4. Systemd (solo Linux)
systemctl status castuo-iot-coop1 castuo-iot-coop2 castuo-iot-coop3 | grep "Active:"
# → Active: active (running) ×3
```

---

## Alertas automáticas IoT — 3 cooperativas

Sistema de alertas críticas: systemd, MQTT, NFT growth y facturación. Ejecución cada 5 min vía cron.

### Script principal

**`scripts/alertas_iot_3_coops.sh`**

1. **Servicios systemd:** Si `castuo-iot-coop1/2/3` no está activo → 🚨 email inmediato.
2. **MQTT:** Por cada coop, espera 1 mensaje (timeout 30 s); si no llega → ⚠️ email silencio.
3. **NFT growth:** Si growth &lt; 9% (token 1, 2 o 3) → ⚠️ email.
4. **Facturación:** Si total último mes &lt; €1.000 → ⚠️ email.

Log: `backend/logs/alertas.log`. Variable: `ALERT_EMAIL` (default `gregorio@castuo.es`).

### Cron

```bash
# Alertas cada 5 min
(crontab -l 2>/dev/null; echo "*/5 * * * * /root/castuo-system/scripts/alertas_iot_3_coops.sh") | crontab -

# Verificación diaria 6:00 (opcional)
(crontab -l 2>/dev/null; echo "0 6 * * * cd /root/castuo-system && ./security/master-encrypt-verify.sh >> /var/log/castuo-salud-diaria.log 2>&1") | crontab -
```

### Umbrales configurados

| Parámetro      | Umbral CRÍTICO   | Umbral AVISO   | Acción        |
|----------------|------------------|----------------|---------------|
| Servicio DOWN  | 0 s              | —              | 🚨 Email      |
| MQTT silencio  | 30 s sin mensaje  | —              | ⚠️ Email      |
| NFT growth     | &lt; 9%           | &lt; 8%         | ⚠️ Email      |
| Facturación   | &lt; €1.000/mes   | &lt; €1.200/mes | ⚠️ Email      |

### Dashboard alertas (web)

**GET http://localhost:8001/alertas**

Devuelve `alertas_activas` (cuenta de líneas con 🚨/⚠️ en las últimas 50 del log) y `ultimas` (últimos 10 eventos).

```bash
curl -s http://localhost:8001/alertas | jq .
```

### Configuración email (Hetzner / Postfix)

```bash
sudo apt install -y postfix mailutils
sudo dpkg-reconfigure postfix   # → Internet Site

# Prueba
echo "Test alerta CASTÚO-SYSTEM" | mail -s "🧪 Test Alertas" gregorio@castuo.es
mailq
```

### Comando único — activar alertas (2 min)

```bash
cd /root/castuo-system
chmod +x scripts/alertas_iot_3_coops.sh
(crontab -l 2>/dev/null; echo "*/5 * * * * /root/castuo-system/scripts/alertas_iot_3_coops.sh") | crontab -
./scripts/alertas_iot_3_coops.sh
curl -s http://localhost:8001/alertas | jq .
tail -f backend/logs/alertas.log
```

### Ejemplo de alerta en log

```
🚨 ALERTAS IoT 3 COOPS - 2026-03-16 04:45
04:45 CRÍTICO: Coop #2 DOWN — systemctl start castuo-iot-coop2.service
04:46 AVISO: Token #3 growth bajo: 8.7% (mín 10%)
📊 2 alertas enviadas - 2026-03-16 04:45
```

### Verificación — dashboard alertas (cada 30 s)

```bash
watch -n 30 '
echo "🔔 ALERTAS 3 COOPS:" && \
tail -5 backend/logs/alertas.log && \
echo "---" && \
curl -s localhost:8001/alertas | jq .alertas_activas && \
echo "Servicios activos:" && \
systemctl is-active castuo-iot-coop1 castuo-iot-coop2 castuo-iot-coop3 2>/dev/null | grep -c running || echo 0
'
```

---

*[IOT_3_COOPS_PRODUCTION](IOT_3_COOPS_PRODUCTION.md) · [FACTURACION_LIVE](FACTURACION_LIVE.md) · [PLAN_COBRO_15_DIAS](PLAN_COBRO_15_DIAS.md)*
