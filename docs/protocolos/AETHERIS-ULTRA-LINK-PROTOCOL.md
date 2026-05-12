# AETHERIS Ultra-Link — protocolo de comunicación y energía nodal

**Objetivo:** viabilidad del nodo Aetheris mediante enlace **ultrarrápido** y **PTM** (Power Transfer Mesh).

## 1. Plano de datos (FSO + fallback)

| Capa | Rol | Objetivo |
|------|-----|----------|
| **FSO primario** | Óptica espacio libre entre nodos / torre / Remolque XXL | **100 Gbps** agregado; inmune a jamming RF convencional. |
| **5G / Sat** | Fallback y telemetría crítica PQC | Continuidad bajo niebla/polvo (FSO degradado). |
| **Mesh láser corto alcance** | Coordinación PTM y handoff | Beam steering + interlock distancia (herencia CASTO láser). |

## 2. PTM (Power Transfer Mesh)

1. Nodo A publica **SoC** y **oferta** de energía (ledger Hyperledger o cola firmada).
2. Nodo B con **SoC &lt;20 %** solicita **sesión PTM**.
3. **Autorización mutua** (firma PQC + geofencing misión).
4. Haz **IR acoplado** (longitud de onda y potencia según normativa); contador de **kWh transferidos** → asiento en smart contract (crédito energético).

## 3. Formato de mensaje (borrador)

```json
{
  "schema": "aetheris.ultralink.v0",
  "from_node": "URN:CASTUO:AETHERIS:...",
  "to_node": "URN:CASTUO:AETHERIS:...",
  "msg_type": "PTM_OFFER|PTM_ACK|FSO_HEARTBEAT",
  "payload_ref": "hash IPFS/WORM",
  "sig_pqc": "..."
}
```

## 4. Implementación en repo

- **API:** `POST /v1/aetheris/ptm/session` — `backend/aetheris/ptm_api.py` (mock tx; conectar Web3/Fabric).
- **Liquidación:** [AETHERIS-PTM-SETTLEMENT.md](../AETHERIS-PTM-SETTLEMENT.md) · `contracts/EnergyCredit.sol`.
- Evento on-chain o canal Fabric: `EnergyCreditSettled(from, to, kwh, mission_id)`.

*Versión v0 — alinear con EASA U-Space y límites exposición láser IR antes de despliegue.*
