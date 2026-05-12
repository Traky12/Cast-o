"""
Nodo 3: PROCESADO — GaiaChain + IPFS
Ancla datos en IPFS y registra hash inmutable en GaiaChain.
Dos escrituras externas → dos compensating actions en rollback_stack.
"""
import sys, os, hashlib, json
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from datetime import datetime, timezone
import httpx
from state import AgroState, CompensatingAction
from tools import tool_register_gaiachain, tool_log_elk, IPFS_API, IPFS_KEY


async def procesado_node(state: AgroState) -> AgroState:
    lote_id = state.get("lote_id", "unknown")
    rollback_stack = list(state.get("rollback_stack", []))

    # Construir registro completo del lote para anclar en IPFS
    record = {
        "lote_id": lote_id,
        "validated_readings": state.get("validated_readings", []),
        "alertas": state.get("readings_alertas", []),
        "sigpac_ref": state.get("sigpac_ref"),
        "traces_cert_id": state.get("traces_cert_id"),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    content_hash = hashlib.sha256(
        json.dumps(record, sort_keys=True, default=str).encode()
    ).hexdigest()

    # 1. Pin a IPFS
    ipfs_cid = await _pin_to_ipfs(record)
    if ipfs_cid:
        ipfs_compensation: CompensatingAction = {
            "node": "procesado",
            "service": "ipfs",
            "action": "unpin",
            "resource_id": ipfs_cid,
            "payload": {"cid": ipfs_cid},
        }
        rollback_stack.append(ipfs_compensation)

    # 2. Registrar en GaiaChain — compensating action incluida en retorno
    # Si GaiaChain falla, IPFS ya está en rollback_stack → LIFO desancla el CID.
    # tx-pending sin blockchain = estado half-committed inaceptable.
    chain_data, chain_compensation = await tool_register_gaiachain(
        lote_id=lote_id,
        content_hash=content_hash,
        ipfs_cid=ipfs_cid or "",
        eco_certified=True,
        operador_nif_hash=state.get("operador_nif", ""),
    )
    tx_hash = chain_data.get("tx_hash")
    if chain_data.get("error") or not tx_hash or tx_hash.startswith("tx-pending-"):
        raise RuntimeError(
            f"GaiaChain registration failed for {lote_id}: "
            f"{chain_data.get('error', 'no confirmed tx_hash')}"
        )
    rollback_stack.append(chain_compensation)

    await tool_log_elk(
        lote_id=lote_id,
        event_type="BLOCKCHAIN_REGISTERED",
        node="procesado",
        data={
            "content_hash": content_hash[:16] + "...",
            "ipfs_cid": ipfs_cid,
            "tx_hash": tx_hash,
        },
    )

    return {
        **state,
        "content_hash": content_hash,
        "ipfs_cid": ipfs_cid,
        "gaiachain_tx_hash": tx_hash,
        "rollback_stack": rollback_stack,
        "current_node": "procesado",
    }


async def _pin_to_ipfs(data: dict) -> str:
    """
    Ancla datos en IPFS. Lanza httpx.RequestError si IPFS no está disponible.
    Sin CID no hay garantía de inmutabilidad — el nodo procesado debe fallar.
    """
    content = json.dumps(data, sort_keys=True, default=str).encode()
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            f"{IPFS_API}/api/v0/add",
            files={"file": ("record.json", content, "application/json")},
            headers={"Authorization": f"Bearer {IPFS_KEY}"},
            params={"pin": "true", "quieter": "true"},
        )
        resp.raise_for_status()
        cid = resp.json().get("Hash")
        if not cid:
            raise ValueError("IPFS no devolvió CID — trazabilidad inmutable comprometida")
        return cid
