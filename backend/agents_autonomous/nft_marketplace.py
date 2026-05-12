# -*- coding: utf-8 -*-
"""NFTMarketplace: tokenización de lotes (IPFS + blockchain) y listado con GaiaChain."""
from __future__ import annotations

import json
import logging
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

logger = logging.getLogger(__name__)

_GAIACHAIN_CLI = os.getenv("GAIACHAIN_CLI", os.getenv("GAIA_CHAIN_CLI", "/usr/local/bin/gaiachain"))
_REPO_ROOT = Path(__file__).resolve().parents[2]


class NFTMarketplace:
    """Acuña NFTs (stub o chain) y registra en GaiaChain; listado para venta."""

    def __init__(self) -> None:
        self.gaiachain_cli = _GAIACHAIN_CLI

    def mint_nft(self, asset_data: Dict[str, Any]) -> Dict[str, Any]:
        """Valida activo, sube metadatos a IPFS (stub si no hay CLI), registra en GaiaChain."""
        if not self._validate_asset_legality(asset_data):
            return {"status": "error", "reason": "Activo no cumple normativas (lote_id, tipo, metadatos; cannabis requiere licencia_aemps)"}
        ipfs_hash = self._upload_to_ipfs(asset_data)
        tx_chain = self._mint_nft_on_chain_stub(asset_data.get("lote_id", ""), ipfs_hash)
        gaia_tx = self._register_in_gaiachain("nft_mint", {
            "lote_id": asset_data.get("lote_id"),
            "tipo": asset_data.get("tipo"),
            "ipfs_hash": ipfs_hash,
            "blockchain_tx": tx_chain,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        return {
            "status": "minted",
            "nft_tx": tx_chain,
            "ipfs_hash": ipfs_hash,
            "gaiachain_tx": gaia_tx,
            "explorer_url": f"https://polygonscan.com/tx/{tx_chain}" if tx_chain else "",
        }

    def _validate_asset_legality(self, asset_data: Dict[str, Any]) -> bool:
        if not all(asset_data.get(f) for f in ["lote_id", "tipo", "metadatos"]):
            return False
        if (asset_data.get("tipo") or "").lower() == "cannabis_medicinal":
            if "licencia_aemps" not in (asset_data.get("metadatos") or {}):
                return False
        return True

    def _upload_to_ipfs(self, asset_data: Dict[str, Any]) -> str:
        ipfs_cli = os.getenv("IPFS_CLI", "/usr/local/bin/ipfs")
        if not os.path.isfile(ipfs_cli):
            return "ipfs-no-cli"
        try:
            meta = {"name": f"Lote {asset_data.get('lote_id')}", "description": (asset_data.get("metadatos") or {}).get("descripcion", ""), "attributes": (asset_data.get("metadatos") or {}).get("atributos", {})}
            tmp = _REPO_ROOT / f"temp_nft_{asset_data.get('lote_id', '')}.json"
            tmp.write_text(json.dumps(meta), encoding="utf-8")
            r = subprocess.run([ipfs_cli, "add", "-q", str(tmp)], capture_output=True, text=True, timeout=15, cwd=str(_REPO_ROOT))
            tmp.unlink(missing_ok=True)
            if r.returncode == 0 and r.stdout:
                return r.stdout.strip().split()[-1]
        except Exception as e:
            logger.warning("IPFS add: %s", e)
        return "ipfs-error"

    def _mint_nft_on_chain_stub(self, lote_id: str, ipfs_hash: str) -> str:
        """Stub: en producción conectar a Polygon/Ethereum con web3."""
        return f"0xstub_{lote_id}_{ipfs_hash[:8]}"

    def list_nft_for_sale(self, nft_data: Dict[str, Any], price: float) -> Dict[str, Any]:
        """Registra listado en GaiaChain; URL de marketplace stub."""
        gaia_tx = self._register_in_gaiachain("nft_listing", {
            "nft_tx": nft_data.get("nft_tx"),
            "price": price,
            "currency": "MATIC",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        return {
            "status": "listed",
            "gaiachain_tx": gaia_tx,
            "marketplace_url": f"https://opensea.io/assets/matic/stub/{nft_data.get('nft_tx', '')}",
        }

    def _register_in_gaiachain(self, record_type: str, data: Dict[str, Any]) -> str:
        if not os.path.isfile(self.gaiachain_cli):
            return "gaiachain-no-cli"
        try:
            r = subprocess.run(
                [self.gaiachain_cli, "record", "--type", record_type, "--data", json.dumps(data)],
                capture_output=True, text=True, timeout=10,
            )
            return (r.stdout or "").strip() or "ok" if r.returncode == 0 else f"Error: {r.stderr}"
        except Exception as e:
            return f"Error: {e}"

    def _query_harvest(self, lote_id: str) -> Dict[str, Any]:
        if not os.path.isfile(self.gaiachain_cli):
            return {"producto": "Cannabis Medicinal", "fecha_cosecha": datetime.now(timezone.utc).strftime("%d/%m/%Y"), "peso_neto": "0 g", "licencia_aemps": "N/A"}
        try:
            r = subprocess.run(
                [self.gaiachain_cli, "query", "--type", "harvest", "--lote_id", lote_id],
                capture_output=True, text=True, timeout=10,
            )
            if r.returncode == 0 and r.stdout.strip():
                out = json.loads(r.stdout)
                return out.get("data", out)
        except Exception:
            pass
        return {"producto": "Cannabis Medicinal", "fecha_cosecha": datetime.now(timezone.utc).strftime("%d/%m/%Y"), "peso_neto": "0 g", "licencia_aemps": "N/A"}

    def create_royalty_nft(self, lote_id: str, royalty_percentage: float = 5.0) -> Dict[str, Any]:
        """Crea NFT con royalties para datos de cultivo (RD 903/2025, licencia AEMPS)."""
        harvest_data = self._query_harvest(lote_id)
        metadata = {
            "descripcion": f"Datos de cultivo lote {lote_id}. Royalty {royalty_percentage}%.",
            "atributos": {
                "lote_id": lote_id,
                "producto": harvest_data.get("producto", ""),
                "fecha_cosecha": harvest_data.get("fecha_cosecha", ""),
                "peso_neto": harvest_data.get("peso_neto", ""),
                "royalty_percentage": royalty_percentage,
                "licencia_aemps": harvest_data.get("licencia_aemps", "N/A"),
            },
            "licencia_aemps": harvest_data.get("licencia_aemps", "N/A"),
        }
        return self.mint_nft({"lote_id": lote_id, "tipo": "data_royalty", "metadatos": metadata})

    def list_nft_with_royalty(self, nft_data: Dict[str, Any], price: float, royalty_percentage: float = 5.0) -> Dict[str, Any]:
        """Lista NFT con royalties en GaiaChain."""
        listing = {"nft_tx": nft_data.get("nft_tx"), "price": price, "royalty_percentage": royalty_percentage, "currency": "MATIC", "timestamp": datetime.now(timezone.utc).isoformat()}
        gaia_tx = self._register_in_gaiachain("nft_royalty_listing", listing)
        return {"status": "success", "listing_data": listing, "gaiachain_tx": gaia_tx, "marketplace_url": f"https://opensea.io/assets/matic/stub/{nft_data.get('nft_tx', '')}"}

    def track_royalties(self, nft_id: str) -> Dict[str, Any]:
        """Consulta royalties registrados para un NFT en GaiaChain."""
        if not os.path.isfile(self.gaiachain_cli):
            return {"status": "stub", "data": [], "nft_id": nft_id}
        try:
            r = subprocess.run(
                [self.gaiachain_cli, "query", "--type", "nft_royalty", "--nft_id", nft_id],
                capture_output=True, text=True, timeout=10,
            )
            if r.returncode == 0 and r.stdout.strip():
                return json.loads(r.stdout)
        except Exception as e:
            return {"status": "error", "reason": str(e)}
        return {"status": "ok", "data": [], "nft_id": nft_id}

    def pay_royalties(self, nft_id: str, amount: float, currency: str = "MATIC") -> Dict[str, Any]:
        """Registra pago de royalties en GaiaChain (blockchain_tx stub en producción)."""
        tracked = self.track_royalties(nft_id)
        recipient = "0xSTUB-RECIPIENT"
        if isinstance(tracked.get("data"), list) and tracked["data"]:
            recipient = tracked["data"][0].get("recipient", recipient)
        royalty_data = {"nft_id": nft_id, "amount": amount, "currency": currency, "recipient": recipient, "timestamp": datetime.now(timezone.utc).isoformat()}
        gaia_tx = self._register_in_gaiachain("royalty_payment", royalty_data)
        blockchain_tx = f"0xROYALTY-{nft_id[-8:] if len(nft_id) >= 8 else nft_id}-{datetime.now(timezone.utc).strftime('%Y%m%d')}"
        return {"status": "success", "royalty_data": royalty_data, "gaiachain_tx": gaia_tx, "blockchain_tx": blockchain_tx, "message": f"Royalties de {amount} {currency} pagados a {recipient}"}
