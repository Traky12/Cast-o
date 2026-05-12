# IoT Monitors — 3 Cooperativas Production (v1.7.2)

Integración IoT en tiempo real para las 3 cooperativas: Sabionda SAT, Cooperativa #2, Cooperativa #3. Growth ~10%/día hacia Dynamic NFT en GaiaChain.

## Contexto

| Cooperativa           | Ha   | Token | Cultivo  |
|-----------------------|------|-------|----------|
| Sabionda Educa SAT    | 2.5  | 1     | lechuga  |
| Cooperativa #2  | 5.0  | 2     | vid      |
| Cooperativa #3  | 3.0  | 3     | tomate   |

- **Backend:** FastAPI puerto 8001; `POST/GET /cooperativas` y `POST /nft/growth` operativos.
- **Security:** 10/10 (Docker secrets + git-crypt).
- **ARR proyectado:** €1.47M (10.5 ha).

## Componentes

1. **`backend/scripts/iot_monitor_3_coops.py`**  
   - Simula sensores (EC, pH, DO, temp, growth).  
   - Publica MQTT en `hidroponia/<coop>/sensors` (opcional).  
   - Llama `POST http://localhost:8001/nft/growth` con `token_id` y `growth`.  
   - Uso:  
     - Una cooperativa: `python backend/scripts/iot_monitor_3_coops.py --coop 1 --interval 86400`  
     - Las 3 en un proceso: `python backend/scripts/iot_monitor_3_coops.py --interval 86400`  
   - Variables: `BACKEND_URL`, `MQTT_HOST`, `MQTT_PORT`, `IOT_GROWTH_RATE_PCT`, `IOT_INTERVAL_SECONDS`, `IOT_MONITOR_LOG`.

2. **`backend/routers/nft.py`**  
   - `POST /nft/growth`: body `{"token_id": 1|2|3, "growth": 0-100}`.  
   - Ejecuta `update_dynamic_nft.py` (IPFS + GaiaChain).  
   - Requiere: `GAIA_CHAIN_RPC`, `DYNAMIC_NFT_ADDRESS`, `PRIVATE_KEY`.

3. **Systemd (Hetzner/Linux)**  
   - Units en `scripts/systemd/`:  
     - `castuo-iot-coop1.service`  
     - `castuo-iot-coop2.service`  
     - `castuo-iot-coop3.service`  
   - Copiar a `/etc/systemd/system/` y ajustar `WorkingDirectory` si el repo no está en `/root/castuo-system`.

4. **`scripts/activar_produccion_3_coops.sh`**  
   - Verificación 10/10, (opcional) instalación de units, sugerencia de mint, deploy docs.  
   - Ejecución: `chmod +x scripts/activar_produccion_3_coops.sh && ./scripts/activar_produccion_3_coops.sh`

## Comando único (production)

```bash
chmod +x scripts/activar_produccion_3_coops.sh && \
./scripts/activar_produccion_3_coops.sh && \
tail -f backend/logs/iot-monitor.log
```

(Si no hay log file, usar `journalctl -u castuo-iot-coop1 -f` etc. en el servidor.)

## Resultado esperado

- Sabionda SAT: Growth ~10%/día, EC/PH simulados, MQTT si broker activo, NFT #1 actualizado.  
- Coop #2 / Coop #3: Igual para tokens 2 y 3.  
- Backend 8001: `/cooperativas`, `/nft/growth` operativos.  
- Security 10/10; ARR €1.47M production live.

**Monitoreo en tiempo real:** [MONITOREO_3_COOPS](MONITOREO_3_COOPS.md) (dashboard terminal, MQTT, alertas).

---

*[MONITOREO_3_COOPS](MONITOREO_3_COOPS.md) · [ESTATUS_VALOR_V1.7.1](ESTATUS_VALOR_V1.7.1.md) · [COOPERATIVAS_3_INTEGRADAS](COOPERATIVAS_3_INTEGRADAS.md) · [COMANDO_UNICO_HETZNER_COOP2](COMANDO_UNICO_HETZNER_COOP2.md)*
