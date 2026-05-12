"""
CASTÚO-SYSTEM™ v3.0 — Servicio QR de Inmutabilidad
Tracking completo desde semilla hasta consumidor.
Cifrado ECC-256 | Anclaje IPFS | Registro GaiaChain
Sin Químicos — Certificación Ecológica Trazable
"""

import base64
import hashlib
import json
import logging
import secrets
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import httpx

from config.global_config import GaiaChainConfig, IPFSConfig, QRConfig

logger = logging.getLogger("castuo.qr")


# Etapas de trazabilidad desde semilla hasta consumidor
TRACKING_STAGES = [
    "semilla",
    "siembra",
    "cultivo",
    "cosecha",
    "procesado",
    "certificacion",
    "embalaje",
    "distribucion",
    "consumidor",
]


@dataclass
class QRTrackingData:
    """Datos embebidos en el QR de trazabilidad."""
    product_id: str
    product_name: str
    current_stage: str
    operator_nif: str
    sigpac_ref: str
    eco_certified: bool
    blockchain_tx: Optional[str] = None   # tx_hash en GaiaChain
    ipfs_cid: Optional[str] = None        # CID del registro completo
    content_hash: Optional[str] = None    # SHA-256 del contenido
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "product_id": self.product_id,
            "product_name": self.product_name,
            "current_stage": self.current_stage,
            "operator_nif": self.operator_nif,
            "sigpac_ref": self.sigpac_ref,
            "eco_certified": self.eco_certified,
            "blockchain_tx": self.blockchain_tx,
            "ipfs_cid": self.ipfs_cid,
            "content_hash": self.content_hash,
            "created_at": self.created_at,
            "metadata": self.metadata,
        }

    def compute_hash(self) -> str:
        """SHA-256 del payload del QR para verificación de integridad."""
        payload = {
            k: v for k, v in self.to_dict().items()
            if k not in ("blockchain_tx", "ipfs_cid", "content_hash")
        }
        return hashlib.sha256(
            json.dumps(payload, sort_keys=True).encode()
        ).hexdigest()


@dataclass
class QRGenerationResult:
    product_id: str
    stage: str
    qr_svg: Optional[str]
    qr_url: str              # URL pública de verificación
    blockchain_tx: Optional[str]
    ipfs_cid: Optional[str]
    content_hash: str
    verify_url: str          # URL de verificación de autenticidad
    generated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class QRTrackingService:
    """
    Servicio de generación y verificación de QR con inmutabilidad blockchain.

    Flujo completo:
    1. Construir QRTrackingData con info del producto y etapa
    2. Calcular SHA-256 del contenido (integridad)
    3. Subir datos completos a IPFS Cluster (3 réplicas UE)
    4. Registrar CID + hash en GaiaChain 3.0
    5. Generar QR SVG con ECC-256 que embebe URL de verificación
    6. Retornar QR + references blockchain + IPFS
    """

    VERIFY_BASE_URL = "https://verify.castuo-system.eu/qr"

    def __init__(
        self,
        qr_config: QRConfig,
        chain_config: GaiaChainConfig,
        ipfs_config: IPFSConfig,
    ) -> None:
        self.qr = qr_config
        self.chain = chain_config
        self.ipfs = ipfs_config
        self._chain_client: Optional[httpx.AsyncClient] = None
        self._ipfs_client: Optional[httpx.AsyncClient] = None
        self._qr_client: Optional[httpx.AsyncClient] = None

    async def close(self) -> None:
        """Cierra clientes HTTP reutilizables."""
        for client in (self._chain_client, self._ipfs_client, self._qr_client):
            if client is not None and not client.is_closed:
                await client.aclose()

    @property
    def _chain_http(self) -> httpx.AsyncClient:
        if self._chain_client is None or self._chain_client.is_closed:
            self._chain_client = httpx.AsyncClient(
                headers={"Authorization": f"Bearer {self.chain.api_key}"},
                timeout=httpx.Timeout(self.chain.timeout),
            )
        return self._chain_client

    @property
    def _ipfs_http(self) -> httpx.AsyncClient:
        if self._ipfs_client is None or self._ipfs_client.is_closed:
            self._ipfs_client = httpx.AsyncClient(
                headers={"Authorization": f"Bearer {self.ipfs.api_key}"},
                timeout=httpx.Timeout(self.ipfs.timeout),
            )
        return self._ipfs_client

    @property
    def _qr_http(self) -> httpx.AsyncClient:
        if self._qr_client is None or self._qr_client.is_closed:
            self._qr_client = httpx.AsyncClient(
                headers={"Authorization": f"Bearer {self.qr.api_key}"},
                timeout=httpx.Timeout(self.qr.timeout),
            )
        return self._qr_client

    # -------------------------------------------------------------------------
    # Product ID Generation
    # -------------------------------------------------------------------------

    @staticmethod
    def generate_product_id(
        explotacion_rea: str,
        cultivo: str,
        campana: str,
        lote: Optional[str] = None,
    ) -> str:
        """
        Genera ID único de producto basado en REA + cultivo + campaña.
        Formato: CS-{REA}-{CULTIVO_HASH}-{CAMPANA}-{RANDOM}
        """
        cultivo_hash = hashlib.sha256(cultivo.lower().encode()).hexdigest()[:6].upper()
        random_suffix = secrets.token_hex(3).upper()
        if lote:
            return f"CS-{explotacion_rea}-{cultivo_hash}-{campana}-{lote}"
        return f"CS-{explotacion_rea}-{cultivo_hash}-{campana}-{random_suffix}"

    # -------------------------------------------------------------------------
    # Core QR Generation
    # -------------------------------------------------------------------------

    async def generate_stage_qr(
        self,
        tracking_data: QRTrackingData,
        pin_to_ipfs: bool = True,
        register_blockchain: bool = True,
    ) -> QRGenerationResult:
        """
        Genera QR para una etapa específica de la cadena de trazabilidad.
        Opcionalmente ancla en IPFS y registra en GaiaChain.
        """
        content_hash = tracking_data.compute_hash()
        tracking_data.content_hash = content_hash

        ipfs_cid: Optional[str] = None
        blockchain_tx: Optional[str] = None

        # 1. Anclar en IPFS
        if pin_to_ipfs:
            ipfs_cid = await self._pin_to_ipfs(tracking_data.to_dict())
            tracking_data.ipfs_cid = ipfs_cid

        # 2. Registrar en GaiaChain
        if register_blockchain:
            blockchain_tx = await self._register_blockchain(tracking_data)
            tracking_data.blockchain_tx = blockchain_tx

        # 3. Construir URL de verificación pública
        verify_url = f"{self.VERIFY_BASE_URL}/{tracking_data.product_id}/{content_hash}"

        # 4. Generar QR SVG
        qr_payload = {
            "verify_url": verify_url,
            "product_id": tracking_data.product_id,
            "stage": tracking_data.current_stage,
            "eco_certified": tracking_data.eco_certified,
            "tx": blockchain_tx,
            "cid": ipfs_cid,
        }
        qr_svg = await self._generate_qr_svg(qr_payload)

        # URL pública del QR (servida por el gateway)
        qr_url = f"{self.ipfs.gateway}/ipfs/{ipfs_cid}" if ipfs_cid else verify_url

        logger.info(
            "QR generated: product=%s stage=%s tx=%s cid=%s",
            tracking_data.product_id,
            tracking_data.current_stage,
            blockchain_tx,
            ipfs_cid,
        )

        return QRGenerationResult(
            product_id=tracking_data.product_id,
            stage=tracking_data.current_stage,
            qr_svg=qr_svg,
            qr_url=qr_url,
            blockchain_tx=blockchain_tx,
            ipfs_cid=ipfs_cid,
            content_hash=content_hash,
            verify_url=verify_url,
        )

    async def generate_full_traceability_qr(
        self,
        product_id: str,
        product_name: str,
        operator_nif: str,
        sigpac_ref: str,
        eco_certified: bool,
        stages_metadata: Optional[Dict[str, Dict[str, Any]]] = None,
    ) -> List[QRGenerationResult]:
        """
        Genera QRs para todas las etapas de trazabilidad del producto.
        Retorna una lista de QRGenerationResult, uno por etapa.
        """
        results = []
        for stage in TRACKING_STAGES:
            meta = (stages_metadata or {}).get(stage, {})
            tracking_data = QRTrackingData(
                product_id=product_id,
                product_name=product_name,
                current_stage=stage,
                operator_nif=operator_nif,
                sigpac_ref=sigpac_ref,
                eco_certified=eco_certified,
                metadata=meta,
            )
            result = await self.generate_stage_qr(tracking_data)
            results.append(result)
        return results

    # -------------------------------------------------------------------------
    # Verification
    # -------------------------------------------------------------------------

    async def verify_qr(
        self, product_id: str, content_hash: str
    ) -> Dict[str, Any]:
        """
        Verifica la autenticidad de un QR consultando GaiaChain.
        Compara el hash presentado con el registrado on-chain.
        """
        contract_address = self.chain.contracts.get("trazabilidad", "")
        response = await self._chain_http.get(
            f"{self.chain.endpoint}/contracts/{contract_address}/query",
            params={
                "function": "verifyTrace",
                "productId": product_id,
                "contentHash": f"0x{content_hash}",
            },
        )
        response.raise_for_status()
        result = response.json()

        return {
            "product_id": product_id,
            "authentic": result.get("valid", False),
            "on_chain_hash": result.get("storedHash"),
            "presented_hash": content_hash,
            "blockchain": "GaiaChain 3.0",
            "verified_at": datetime.now(timezone.utc).isoformat(),
        }

    # -------------------------------------------------------------------------
    # Internal Helpers
    # -------------------------------------------------------------------------

    async def _pin_to_ipfs(self, data: Dict[str, Any]) -> str:
        """Sube datos a IPFS y retorna el CID."""
        content = json.dumps(data, sort_keys=True, ensure_ascii=False).encode()
        response = await self._ipfs_http.post(
            f"{self.ipfs.endpoint}/api/v0/add",
            files={"file": ("qr_data.json", content, "application/json")},
            params={"pin": "true", "quieter": "true"},
        )
        response.raise_for_status()
        result = response.json()
        return result.get("Hash") or result.get("cid", {}).get("/", "")

    async def _register_blockchain(self, data: QRTrackingData) -> Optional[str]:
        """Registra el QR en GaiaChain y retorna el tx_hash."""
        contract_address = self.chain.contracts.get("trazabilidad", "")
        response = await self._chain_http.post(
            f"{self.chain.endpoint}/contracts/{contract_address}/call",
            headers={"X-Chain-ID": str(self.chain.chain_id)},
            json={
                "function": "registerQR",
                "params": {
                    "productId": data.product_id,
                    "stage": data.current_stage,
                    "contentHash": f"0x{data.content_hash}",
                    "ipfsCid": data.ipfs_cid or "",
                    "ecoCertified": data.eco_certified,
                    "operatorNif": data.operator_nif,
                },
            },
        )
        response.raise_for_status()
        return response.json().get("tx_hash")

    async def _generate_qr_svg(self, payload: Dict[str, Any]) -> Optional[str]:
        """Llama al microservicio QR Generator y retorna el SVG en base64."""
        try:
            response = await self._qr_http.post(
                f"{self.qr.endpoint}/generate",
                json={
                    "data": json.dumps(payload),
                    "format": self.qr.output_format,
                    "encryption": self.qr.encryption,
                    "error_correction": "H",  # Alta corrección de errores
                },
            )
            response.raise_for_status()
            result = response.json()
            return result.get("svg") or result.get("data")
        except Exception as exc:
            logger.warning("QR generator unavailable, skipping SVG: %s", exc)
            # Fallback: retornar representación textual del payload
            fallback = base64.b64encode(
                json.dumps(payload).encode()
            ).decode()
            return fallback
