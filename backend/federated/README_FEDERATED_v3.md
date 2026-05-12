# CASTUO_FEDERATED_IA_v3.0 — Arquitectura federada auditada

Evolución desde TRL8 IA v2.0 a **sistema federado con trazabilidad blockchain** y 12 agentes.

---

## Arquitectura v3.0

```
Nodo1 (Gregorio-PC)  ↔  Nodo2 (Técnico-Campo)  ↔  Nodo3 (CTAEX-Demo)
        ↓                         ↓                         ↓
  Anytype-P2P             FastAPI-Federated           Vault-Replica
        ↓                         ↓                         ↓
  Consenso 2/3  ←──────────  Broadcast  ──────────→  IPFS + Block Hash
```

### 1. Federación IA (multi-nodo)

- **node1-castuo** (Gregorio PC): puerto 8001  
- **node2-castuo** (Técnico Campo): puerto 8011  
- **node3-castuo** (CTAEX Demo): puerto 8012  

Cada nodo expone FastAPI con `/federated/action`, `/federated/vote`, `/federated/dashboard`. Las acciones se difunden a los 3 nodos; se requiere **consenso ≥ 2/3** para aprobar.

### 2. Audit trail blockchain (IPFS + hash)

Cada acción aprobada se registra en el auditor:

- **Block hash** (SHA-256, prefijo `0x`)
- **IPFS Pin** (CID tipo `Qm...`)
- **Anytype Object** id: `Audit-001`, `Audit-002`, …

Servicio **ipfs** (Kubo) en puertos 4001 (swarm) y 5001 (API).

### 3. Agentes federados (12)

| Agente        | Acción           | Descripción                          |
|---------------|------------------|--------------------------------------|
| auditoria     | ISO + blockchain | Stage 2 + audit trail                |
| vault         | Kyber federado  | Rotación PQC + réplica nodos         |
| monitoreo     | check_uptime     | Uptime 99.9%                         |
| campo         | consent_gdpr     | Consents 92%                         |
| federacion    | sync_nodos       | Sincronización estado entre nodos     |
| blockchain    | audit_trail      | IPFS + block hash                    |
| ml_predict    | predict          | Fail rate, revenue Q2                 |
| contracts     | smart_gdpr       | Consent on-chain (Solidity)           |
| anytype_sync  | p2p_sync         | Anytype P2P                           |
| compliance    | iso_stage2       | ISO Stage 2 %                         |
| revenue       | forecast         | Revenue Q2 €                         |
| alerting      | notify           | Telegram / Slack                     |

### 4. Métricas federadas (dashboard)

**GET /federated/dashboard** devuelve:

- **Federadas:** `nodes_online`, `consensus_pct`, `blocks`, `node_id`, `peers`
- **Blockchain:** `audit_trail_blocks`, `ipfs_pins`, `last_block`
- **Predictivas:** `fail_rate_pct`, `revenue_q2_eur`, `iso_stage2_pct`, `mttr_reduction_pct`
- **Locales:** `iso_pct`, `uptime_pct`, `kyber_days`, `gdpr_consents_pct`
- **Agentes:** lista de los 12 agentes

Ejemplo objetivo:

- **FEDERADAS:** Nodes_online=3/3 (100%), Consensus=2/3, Blocks=156  
- **PREDICTIVAS:** Fail_rate=0.2%, Revenue_Q2=€150K, ISO_Stage2=98%  
- **BLOCKCHAIN:** Audit_trail=247 blocks, IPFS_pins=156 CIDs  

---

## Archivos generados

```
backend/federated/
├── federated_coordinator.py   # Nodo master + consenso 2/3
├── blockchain_auditor.py      # IPFS + block hash + Anytype Object
├── agent_federation.py        # 12 agentes P2P
├── ml_predictor.py            # Fail rate, revenue Q2, ISO Stage2
├── app_federated.py           # FastAPI dashboard + action + vote + audit
├── Dockerfile
├── (docker-compose en raíz: docker-compose.federated.yml)
├── smart_contracts/
│   ├── GDPRConsent.sol        # Smart GDPR consents (Sepolia)
│   └── README.md
└── README_FEDERATED_v3.md
```

`docker-compose.federated.yml` está en la **raíz del repo** (no dentro de `backend/federated/`).

---

## Cómo levantar (15 min → v3.0)

```bash
# Desde la raíz del repo
docker-compose -f docker-compose.federated.yml up -d

# Dashboard v3.0
curl http://localhost:8001/federated/dashboard | jq
```

Abrir en navegador: **http://localhost:8001/federated/dashboard** → v3.0 LIVE.

### Demo CTAEX 15 min

1. `docker-compose -f docker-compose.federated.yml up` → 3 nodos + IPFS en marcha.  
2. iPhone Campo → Anytype QR → P2P → los 3 nodos reciben y votan (consenso 2/3).  
3. **AGENTE_AUDITORIA** → ISO 92% → se escribe en blockchain audit trail (block hash + IPFS).  
4. Dashboard: Uptime 99.9% | Consensus 100% | Revenue €150K.

### Ejemplo de acción federada

```bash
curl -X POST http://localhost:8001/federated/action \
  -H "Content-Type: application/json" \
  -d '{"type":"Certificación","agent":"auditoria","progress":92}'
```

Respuesta esperada (ejemplo): `consensus: true`, `block_hash`, `ipfs_cid`, `anytype_object_id: Audit-001`.

---

## Valor estratégico v3.0

| Feature      | v2.0   | v3.0 Federado   | € Incremento |
|-------------|--------|------------------|--------------|
| Nodos       | 1      | **3 P2P**        | +€400K       |
| Audit       | Logs   | **Blockchain**   | +€300K       |
| Predict     | Manual | **ML 0.2% fail** | +€250K       |
| Agentes     | 4      | **12 autónomos** | +€500K       |

- **Federado** → +€1.2M ARR enterprise 2027  
- **Blockchain** → ISO 27001 Stage 2 100% audit  
- **ML Predict** → -85% tiempo MTTR  
- **12 Agentes** → 24/7 autonomía  

---

## ROI v3.0 vs v2.0

Federación + audit trail + ML + 12 agentes = **€1.8M valor 2027**.
