# ENLACES DE TRAZABILIDAD (coherencia con el repo)

## 1) Documentacion relacionada

Para el marco completo de seguridad reforzada:
- `ARQUITECTURA-SEGURIDAD-REFORZADA-QUBES-WHONIX-PARROT.md`
- `PRONTUARIO_MAESTRO_EVOLUTIVO_ECSE.md` (ver la seccion `Trazabilidad con Monitoreo y Diagnostico`)
- `PRONTUARIO_MAESTRO_MONITOREO_DIAGNOSTICO_TRL9.md` (ver la seccion `Relacion con ECSE (marco evolutivo)`)
- `scripts/Register-SecurityEvent.ps1` (evidencia inmutable via GaiaChain witness)

## 2) Matriz de severidad normalizada (compatible con backend/scripts)

Notas de coherencia con este repo:
- Para registrar un evento critico en la base local (SQLite), se usa: `POST /agents/system/log-event`
- Para registrar evidencia inmutable en GaiaChain, se usa: `POST $GAIA_CHAIN_API_URL/api/v1/witness` via `scripts/Register-SecurityEvent.ps1`
- `severity` soporta exactamente: `critical|error|warning|info`

| Tipo de Evento | Severidad | Registro local (endpoint) | Accion recomendada (ejemplo) | Responsable | TXID GaiaChain |
|---|---|---|---|---|---|
| unauthorized_access_attempt | critical | POST `/agents/system/log-event` | Bloquear IP en firewall, rotar credenciales, auditar logs. | Seguridad | txid desde `Register-SecurityEvent.ps1` |
| failed_login_attempt | warning | POST `/agents/system/log-event` | Monitorear patrones, verificar credenciales comprometidas. | Seguridad | txid desde `Register-SecurityEvent.ps1` |
| database_connection_failed | error | POST `/agents/system/log-event` | Revisar conexion a base de datos, verificar backups. | DBA | txid desde `Register-SecurityEvent.ps1` |
| gaiachain_connection_error | error | POST `/agents/system/log-event` | Verificar conectividad GaiaChain y revisar evidencia de sincronizacion. | DevOps | txid desde `Register-SecurityEvent.ps1` |
| whonix_tor_circuit_failed | critical | POST `/agents/system/log-event` | Reiniciar Whonix-Gateway, verificar configuracion Tor (evidencia via logs/monitoreo). | Seguridad | txid desde `Register-SecurityEvent.ps1` |
| parrot_vulnerability_detected | error | POST `/agents/system/log-event` | Revisar informe OpenVAS/Wazuh y aplicar parches. | Seguridad | txid desde `Register-SecurityEvent.ps1` |
| qubes_vm_isolation_breach | critical | POST `/agents/system/log-event` | Aislar VM afectada, revisar logs de Qubes y hardening. | Seguridad | txid desde `Register-SecurityEvent.ps1` |
| emergency_protocol_activated | critical | POST `/agents/system/log-event` | Evento generado automaticamente por `scripts/emergency_protocol.ps1` cuando GaiaChain permanece offline > umbral. | Seguridad | txid opcional desde `Register-SecurityEvent.ps1` |

## 3) Contrato de GaiaChain witness (verificado contra el repo)

`scripts/Register-SecurityEvent.ps1` construye el payload minimal del witness asi:

```powershell
$payloadWitness = @{
  hash = $eventHash      # SHA256 del metadata canono (string JSON)
  coop_id = $CoopId      # default 1
  ipfs_cid = $null       # IPFS opcional (no usado aqui)
}

$witnessUrl = ($GaiaChainApiUrl.TrimEnd("/")) + "/api/v1/witness"
$response = Invoke-RestMethod -Uri $witnessUrl -Method Post -Headers @{
  "Authorization" = "Bearer $GaiaChainApiKey"
  "Content-Type" = "application/json"
} -Body ($payloadWitness | ConvertTo-Json -Depth 20 -Compress)
```

Campos/verificacion:
- Endpoint: `/api/v1/witness`
- Payload: `hash`, `coop_id`, `ipfs_cid`

## 4) Checklist de verificacion de coherencia (repo)

### 4.1 Verificar el endpoint witness (ejemplo)

```bash
curl -X POST "$GAIA_CHAIN_API_URL/api/v1/witness" \
  -H "Authorization: Bearer $GAIA_CHAIN_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "coop_id": 1,
    "hash": "a1b2c3...sha256_del_metadata_canono...",
    "ipfs_cid": null
  }'
```

### 4.2 Ejecutar el script de evidencia

```powershell
.\scripts\Register-SecurityEvent.ps1 `
  -EventType "system_test" `
  -EventData @{ message="Prueba de integration"; status="success" } `
  -Severity "info" `
  -CoopId 1 `
  -LogEventInBackend
```

### 4.3 Confirmar resultados esperados
- Verificar que se crea evidencia local en: `security-events/<yyyyMMdd>/<txid>.json`
- Si el backend esta accesible y `-LogEventInBackend`, verificar que `POST /agents/system/log-event` responda `status=success`.

---

## 5) Documentos que conectan la trazabilidad
- `docs/PRONTUARIO_MAESTRO_EVOLUTIVO_ECSE.md` -> seccion `Trazabilidad con Monitoreo y Diagnostico`
- `docs/PRONTUARIO_MAESTRO_MONITOREO_DIAGNOSTICO_TRL9.md` -> seccion `Relacion con ECSE (marco evolutivo)`
- `docs/ARQUITECTURA-SEGURIDAD-REFORZADA-QUBES-WHONIX-PARROT.md` -> seccion `Documento maestro de seguridad reforzada`

---

## 6) Evidencia legal verificable (certificados soberanos)

El backend expone verificacion publica de certificados soberanos (compatibles con QR/enlaces de verificacion):

- `GET /agents/certificates/verify/{tx_hash}`
- `GET /agents/certificates/verify?tx_hash={tx_hash}` (compatibilidad con query param)

Alias publico adicional:
- `GET /api/certificates/verify/{tx_hash}` (si el parametro parece un TXID GaiaChain)

Ejemplo:

```bash
curl "http://localhost:8001/agents/certificates/verify/0xTU_TX_HASH"
```

o:

```bash
curl "http://localhost:8001/agents/certificates/verify?tx_hash=0xTU_TX_HASH"
```

---

## 7) Enlaces bidireccionales

- Desde `docs/ARQUITECTURA-SEGURIDAD-REFORZADA-QUBES-WHONIX-PARROT.md` se enlaza a este documento en `11) Enlaces de trazabilidad`.

## 8) Evidencia legal verificada

- `docs/EVIDENCIA-LEGAL-VERIFICADA.md`


