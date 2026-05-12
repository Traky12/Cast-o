"""
CASTÚO-SYSTEM™ v3.0 — GaiaChain 3.0 Client
Blockchain europea soberana para inmutabilidad y trazabilidad agrícola.
Contratos: Trazabilidad · GeoTrace · Certificados
Consenso: Proof of Authority (PoA) — conforme AI Act UE
"""

import hashlib
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Optional

import httpx

from config.global_config import GaiaChainConfig, IPFSConfig
from services.http_client import RetryPolicy, build_async_client, request_with_retry

logger = logging.getLogger("castuo.blockchain")


@dataclass
class TraceabilityRecord:
    """Registro de trazabilidad desde semilla hasta consumidor."""
    product_id: str
    stage: str  # semilla | siembra | cultivo | cosecha | procesado | certificacion | embalaje | distribucion | consumidor
    operator_nif: str
    location_sigpac: str
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)
    eco_certified: bool = False  # Certificación sin químicos

    def to_dict(self) -> Dict[str, Any]:
        return {
            "product_id": self.product_id,
            "stage": self.stage,
            "operator_nif": self.operator_nif,
            "location_sigpac": self.location_sigpac,
            "timestamp": self.timestamp,
            "metadata": self.metadata,
            "eco_certified": self.eco_certified,
        }

    def content_hash(self) -> str:
        """SHA-256 del contenido del registro — integridad verificable."""
        content = json.dumps(self.to_dict(), sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()


@dataclass
class BlockchainTransaction:
    tx_hash: str
    contract: str
    block_number: int
    timestamp: str
    ipfs_cid: Optional[str] = None
    content_hash: Optional[str] = None


class GaiaChainClient:
    """
    Cliente GaiaChain 3.0 para registro inmutable de trazabilidad agrícola.

    Flujo de registro:
    1. Serializar evento → calcular hash SHA-256
    2. Subir a IPFS Cluster (3 réplicas UE)
    3. Registrar CID + hash en smart contract GaiaChain
    4. Retornar tx_hash para QR embedding
    """

    def __init__(
        self,
        chain_config: GaiaChainConfig,
        ipfs_config: IPFSConfig,
    ) -> None:
        self.chain = chain_config
        self.ipfs = ipfs_config
        self._client: Optional[httpx.AsyncClient] = None
        self._ipfs_client: Optional[httpx.AsyncClient] = None
        self._retry_policy = RetryPolicy(attempts=2, base_delay_seconds=0.4)

    @property
    def client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = build_async_client(
                headers={
                    "Authorization": f"Bearer {self.chain.api_key}",
                    "Content-Type": "application/json",
                    "X-Chain-ID": str(self.chain.chain_id),
                },
                timeout=httpx.Timeout(self.chain.timeout),
            )
        return self._client

    @property
    def ipfs_client(self) -> httpx.AsyncClient:
        if self._ipfs_client is None or self._ipfs_client.is_closed:
            self._ipfs_client = build_async_client(
                headers={"Authorization": f"Bearer {self.ipfs.api_key}"},
                timeout=httpx.Timeout(self.ipfs.timeout),
            )
        return self._ipfs_client

    async def close(self) -> None:
        if self._client and not self._client.is_closed:
            await self._client.aclose()
        if self._ipfs_client and not self._ipfs_client.is_closed:
            await self._ipfs_client.aclose()

    # -------------------------------------------------------------------------
    # IPFS Operations
    # -------------------------------------------------------------------------

    async def pin_to_ipfs(self, data: Dict[str, Any]) -> str:
        """
        Sube datos a IPFS Cluster con replicación mínima de 3 nodos UE.
        Retorna el CID del contenido.
        """
        content = json.dumps(data, sort_keys=True, ensure_ascii=False).encode()
        response = await request_with_retry(
            self.ipfs_client,
            "POST",
            f"{self.ipfs.endpoint}/api/v0/add",
            files={"file": ("record.json", content, "application/json")},
            params={"pin": "true", "quieter": "true"},
            retry_policy=self._retry_policy,
        )
        response.raise_for_status()
        result = response.json()
        cid = result.get("Hash") or result.get("cid", {}).get("/", "")
        logger.info("IPFS pin successful: CID=%s", cid)
        return cid

    def get_ipfs_gateway_url(self, cid: str) -> str:
        return f"{self.ipfs.gateway}/ipfs/{cid}"

    # -------------------------------------------------------------------------
    # Smart Contract Interactions
    # -------------------------------------------------------------------------

    async def register_traceability(
        self, record: TraceabilityRecord
    ) -> BlockchainTransaction:
        """
        Registra un evento de trazabilidad en el contrato GaiaChain.
        Ancla datos en IPFS y registra el CID on-chain.
        """
        record_dict = record.to_dict()
        content_hash = record.content_hash()

        # 1. Anclar en IPFS
        ipfs_cid = await self.pin_to_ipfs(record_dict)

        # 2. Registrar en smart contract de trazabilidad
        contract_address = self.chain.contracts["trazabilidad"]
        response = await request_with_retry(
            self.client,
            "POST",
            f"{self.chain.endpoint}/contracts/{contract_address}/call",
            json={
                "function": "registerTrace",
                "params": {
                    "productId": record.product_id,
                    "stage": record.stage,
                    "operatorNif": record.operator_nif,
                    "locationSigpac": record.location_sigpac,
                    "contentHash": f"0x{content_hash}",
                    "ipfsCid": ipfs_cid,
                    "ecoCertified": record.eco_certified,
                    "timestamp": record.timestamp,
                },
            },
            retry_policy=self._retry_policy,
        )
        response.raise_for_status()
        tx_data = response.json()

        return BlockchainTransaction(
            tx_hash=tx_data.get("tx_hash", ""),
            contract=contract_address,
            block_number=tx_data.get("block_number", 0),
            timestamp=datetime.now(timezone.utc).isoformat(),
            ipfs_cid=ipfs_cid,
            content_hash=content_hash,
        )

    async def register_geo_trace(
        self,
        product_id: str,
        sigpac_ref: str,
        latitude: float,
        longitude: float,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> BlockchainTransaction:
        """Registra localización GPS/SIGPAC en el contrato GeoTrace."""
        contract_address = self.chain.contracts["geotrace"]
        payload: Dict[str, Any] = {
            "productId": product_id,
            "sigpacRef": sigpac_ref,
            "latitude": latitude,
            "longitude": longitude,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        if metadata:
            payload["metadata"] = metadata

        response = await request_with_retry(
            self.client,
            "POST",
            f"{self.chain.endpoint}/contracts/{contract_address}/call",
            json={"function": "registerGeoPoint", "params": payload},
            retry_policy=self._retry_policy,
        )
        response.raise_for_status()
        tx_data = response.json()
        return BlockchainTransaction(
            tx_hash=tx_data.get("tx_hash", ""),
            contract=contract_address,
            block_number=tx_data.get("block_number", 0),
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

    async def issue_certificate(
        self,
        holder_nif: str,
        cert_type: str,  # GlobalGAP | GRASP | ISO14001 | ECO | TRACES
        valid_from: str,
        valid_until: str,
        issuer: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> BlockchainTransaction:
        """
        Emite un certificado digital inmutable en GaiaChain.
        Compatible con eIDAS para firma electrónica europea.
        """
        contract_address = self.chain.contracts["certificados"]
        cert_data: Dict[str, Any] = {
            "holderNif": holder_nif,
            "certType": cert_type,
            "validFrom": valid_from,
            "validUntil": valid_until,
            "issuer": issuer,
            "issuedAt": datetime.now(timezone.utc).isoformat(),
        }
        if metadata:
            cert_data["metadata"] = metadata

        # Anclar certificado completo en IPFS
        ipfs_cid = await self.pin_to_ipfs(cert_data)
        cert_hash = hashlib.sha256(
            json.dumps(cert_data, sort_keys=True).encode()
        ).hexdigest()

        response = await request_with_retry(
            self.client,
            "POST",
            f"{self.chain.endpoint}/contracts/{contract_address}/call",
            json={
                "function": "issueCertificate",
                "params": {
                    **cert_data,
                    "contentHash": f"0x{cert_hash}",
                    "ipfsCid": ipfs_cid,
                },
            },
            retry_policy=self._retry_policy,
        )
        response.raise_for_status()
        tx_data = response.json()
        return BlockchainTransaction(
            tx_hash=tx_data.get("tx_hash", ""),
            contract=contract_address,
            block_number=tx_data.get("block_number", 0),
            timestamp=datetime.now(timezone.utc).isoformat(),
            ipfs_cid=ipfs_cid,
            content_hash=cert_hash,
        )

    async def verify_record(
        self, product_id: str, content_hash: str
    ) -> Dict[str, Any]:
        """Verifica la integridad de un registro comparando el hash on-chain."""
        contract_address = self.chain.contracts["trazabilidad"]
        response = await request_with_retry(
            self.client,
            "GET",
            f"{self.chain.endpoint}/contracts/{contract_address}/query",
            params={
                "function": "verifyTrace",
                "productId": product_id,
                "contentHash": f"0x{content_hash}",
            },
            retry_policy=self._retry_policy,
        )
        response.raise_for_status()
        result = response.json()
        return {
            "product_id": product_id,
            "valid": result.get("valid", False),
            "on_chain_hash": result.get("storedHash"),
            "verified_at": datetime.now(timezone.utc).isoformat(),
        }

    async def get_full_trace(self, product_id: str) -> Dict[str, Any]:
        """Obtiene el historial completo de trazabilidad de un producto."""
        contract_address = self.chain.contracts["trazabilidad"]
        response = await request_with_retry(
            self.client,
            "GET",
            f"{self.chain.endpoint}/contracts/{contract_address}/query",
            params={"function": "getFullTrace", "productId": product_id},
            retry_policy=self._retry_policy,
        )
        response.raise_for_status()
        trace_data = response.json()
        return {
            "product_id": product_id,
            "trace_stages": trace_data.get("stages", []),
            "ipfs_records": [
                self.get_ipfs_gateway_url(stage["ipfsCid"])
                for stage in trace_data.get("stages", [])
                if stage.get("ipfsCid")
            ],
            "verified": trace_data.get("allHashesValid", False),
        }
