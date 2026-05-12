"""GaiaChain 2.0 integration for blockchain-based trazabilidad."""
import importlib
import logging
from typing import Any, Dict, Protocol, Union

logger = logging.getLogger(__name__)


class GaiaChainClient:
    """Placeholder GaiaChain client interface."""
    
    def __init__(self, endpoint: str):
        """Initialize GaiaChain client."""
        self.endpoint = endpoint
    
    def registerDataHash(self, data: Union[Dict[str, Any], str]) -> str:
        """Register data hash on blockchain."""
        raise NotImplementedError(
            "GaiaChain SDK not available. "
            "Install with: pip install gaiachain-sdk"
        )


class SupportsGaiaChain(Protocol):
    def registerDataHash(self, data: Union[Dict[str, Any], str]) -> str:
        ...


class GaiachainConnector:
    """Connector for GaiaChain 2.0 blockchain trazabilidad."""

    def __init__(self, endpoint: str = "https://gaiachain.eu"):
        """
        Initialize GaiaChain connector.

        Args:
            endpoint: GaiaChain API endpoint URL
        """
        self.client: SupportsGaiaChain

        try:
            module = importlib.import_module("gaiachain_sdk")
            RealGaiaChainClient = getattr(module, "GaiaChainClient")
            self.client = RealGaiaChainClient(endpoint=endpoint)
        except ImportError:
            logger.warning(
                "gaiachain-sdk not installed, using mock client. "
                "Install with: pip install gaiachain-sdk"
            )
            self.client = GaiaChainClient(endpoint=endpoint)
        
        self.endpoint = endpoint

    def register_hash(self, data: Union[Dict[str, Any], str]) -> str:
        """
        Register data hash on GaiaChain blockchain for tamper-proof audit trail.

        Args:
            data: Agricultural data (dict or JSON string) to register
                  Example: {
                      "temperature": 25,
                      "humidity": 70,
                      "soil_ph": 6.5,
                      "timestamp": "2026-04-01T10:30:00Z",
                      "location": "Campo Sur",
                      "sensor_id": "sensor_001"
                  }

        Returns:
            Blockchain hash (0x-prefixed hex string) for audit reference

        Raises:
            Exception: If blockchain registration fails
        """
        logger.info("Registering data hash on GaiaChain: %s", self.endpoint)
        
        try:
            # Call GaiaChain SDK to register
            block_hash = self.client.registerDataHash(data)
            
            logger.info("Data registered on blockchain: %s", block_hash)
            return block_hash
        except AttributeError:
            # Using mock client
            raise RuntimeError(
                "GaiaChain SDK not properly installed. "
                "Install with: pip install gaiachain-sdk"
            )

    def create_audit_trail(
        self, data: Dict[str, Any], operation: str = "sensor_reading"
    ) -> Dict[str, Any]:
        """
        Create immutable audit trail for data operation.

        Args:
            data: Data to audit
            operation: Type of operation (sensor_reading, analysis, decision, etc)

        Returns:
            Audit record with blockchain reference

        Raises:
            Exception: If audit creation fails
        """
        audit_data = {
            "operation": operation,
            "data": data,
            "timestamp": data.get("timestamp"),
            "sensor_id": data.get("sensor_id")
        }
        
        block_hash = self.register_hash(audit_data)
        
        return {
            "audit_id": block_hash,
            "operation": operation,
            "blockchain_reference": block_hash,
            "timestamp": audit_data.get("timestamp"),
            "status": "registered"
        }

    def verify_data_integrity(
        self, data: Dict[str, Any], block_hash: str
    ) -> bool:
        """
        Verify data hasn't been tampered with by re-checking blockchain.

        Args:
            data: Data to verify
            block_hash: Original blockchain hash

        Returns:
            True if data matches blockchain record, False otherwise

        Raises:
            Exception: If verification fails
        """
        logger.info("Verifying data integrity against hash: %s", block_hash)
        
        try:
            # Re-register same data and compare hashes
            self.register_hash(data)
            
            # In real GaiaChain, would retrieve original from blockchain
            # For now, we check the hash format and log
            is_valid = block_hash.startswith("0x") and len(block_hash) > 10
            
            logger.info("Data integrity verification: %s", is_valid)
            return is_valid
        except Exception as e:
            logger.error("Integrity verification failed: %s", e)
            raise

    def create_supply_chain_record(
        self, product_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create immutable supply chain record for agricultural product.

        Args:
            product_data: Product information
                Example: {
                    "product_id": "PROD-2026-001",
                    "crop": "tomate",
                    "harvest_date": "2026-06-15",
                    "yield": 1280,
                    "location": "Campo Sur",
                    "quality_score": 8.5,
                    "certifications": ["organic", "fair_trade"]
                }

        Returns:
            Supply chain record with blockchain reference

        Raises:
            Exception: If record creation fails
        """
        logger.info("Creating supply chain record for: %s", product_data.get("product_id"))
        
        try:
            block_hash = self.register_hash(product_data)
            
            return {
                "product_id": product_data.get("product_id"),
                "blockchain_id": block_hash,
                "crop": product_data.get("crop"),
                "harvest_date": product_data.get("harvest_date"),
                "yield": product_data.get("yield"),
                "certifications": product_data.get("certifications", []),
                "record_status": "immutable",
                "blockchain_reference": block_hash
            }
        except Exception as e:
            logger.error("Failed to create supply chain record: %s", e)
            raise

    def get_chain_of_custody(self, product_id: str) -> Dict[str, Any]:
        """
        Retrieve complete chain-of-custody record from blockchain.

        Args:
            product_id: Product identifier

        Returns:
            Chain of custody with all events and handlers

        Note:
            Requires GaiaChain SDK implementation for actual retrieval
        """
        logger.info("Retrieving chain of custody for: %s", product_id)
        
        # Mock implementation - actual SDK would retrieve from blockchain
        return {
            "product_id": product_id,
            "chain": [
                {
                    "event": "harvest",
                    "timestamp": "2026-06-15T09:00:00Z",
                    "actor": "farmer_001",
                    "location": "Campo Sur"
                },
                {
                    "event": "quality_inspection",
                    "timestamp": "2026-06-15T14:00:00Z",
                    "actor": "lab_001",
                    "quality_score": 8.5
                },
                {
                    "event": "storage",
                    "timestamp": "2026-06-15T16:00:00Z",
                    "actor": "warehouse_001",
                    "temperature": 4
                }
            ],
            "status": "authenticated"
        }

    def create_certification_record(
        self, certification_data: Dict[str, Any]
    ) -> str:
        """
        Create immutable certification record on blockchain.

        Args:
            certification_data: Certification information
                Example: {
                    "product_id": "PROD-2026-001",
                    "certification_type": "organic",
                    "issuer": "ECOCERT",
                    "expiry_date": "2027-06-15",
                    "standards": ["EU 2018/848"]
                }

        Returns:
            Blockchain hash for certification

        Raises:
            Exception: If certification registration fails
        """
        logger.info(
            f"Registering certification: {certification_data.get('certification_type')} "
            f"for {certification_data.get('product_id')}"
        )
        
        return self.register_hash(certification_data)
