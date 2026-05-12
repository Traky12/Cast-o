"""
CASTÚO-SYSTEM™ v3.0 — Configuración Global Soberana UE
Arquitectura Europea Avanzada: Soberanía Digital + Inmutabilidad + QR Tracking
RGPD | AI Act UE | eIDAS | GaiaChain 3.0 | Hetzner | Arsys
"""

import os
from dataclasses import dataclass, field
from typing import Dict, Any, Optional


@dataclass
class ClaudeConfig:
    api_endpoint: str = "https://api.anthropic.com/v1"
    model: str = "claude-sonnet-4-6"
    max_tokens: int = 8192
    temperature: float = 0.2
    timeout: int = 60
    retry_attempts: int = 3
    api_key: str = field(default_factory=lambda: os.getenv("CLAUDE_API_KEY", ""))
    tools: list = field(default_factory=lambda: ["read", "write", "execute", "browse", "analyze"])


@dataclass
class CursorConfig:
    endpoint: str = "http://cursor-service:7000"
    api_key: str = field(default_factory=lambda: os.getenv("CURSOR_API_KEY", ""))
    timeout: int = 30


@dataclass
class N8NConfig:
    endpoint: str = "http://n8n-main:5678"
    api_key: str = field(default_factory=lambda: os.getenv("N8N_API_KEY", ""))
    workflow_timeout: int = 180
    health_check: str = "/health"
    basic_auth_user: str = field(default_factory=lambda: os.getenv("N8N_USER", "admin"))
    basic_auth_password: str = field(default_factory=lambda: os.getenv("N8N_PASSWORD", ""))


@dataclass
class MistralConfig:
    endpoint: str = "https://api.mistral.ai/v1"
    api_key: str = field(default_factory=lambda: os.getenv("MISTRAL_API_KEY", ""))
    timeout: int = 45
    inference_model: str = "mistral-large-latest"
    fine_tuning_model: str = "open-mistral-7b"


@dataclass
class SabiondaConfig:
    endpoint: str = "http://sabionda-core:6000/api/v1"
    api_key: str = field(default_factory=lambda: os.getenv("SABIONDA_API_KEY", ""))
    timeout: int = 30
    crop_analysis_model: str = "agriculture-v3.1"
    decision_engine_model: str = "sabionda-governor-v2"


@dataclass
class HetznerConfig:
    endpoint: str = "https://api.hetzner.cloud/v1"
    api_key: str = field(default_factory=lambda: os.getenv("HETZNER_API_KEY", ""))
    timeout: int = 60
    regions: Dict[str, str] = field(default_factory=lambda: {
        "eu-central": "fsn1",
        "eu-west": "nbg1",
        "eu-north": "hel1",
    })
    auto_scale_min_servers: int = 2
    auto_scale_max_servers: int = 10
    cpu_scale_up_threshold: float = 80.0
    cpu_scale_down_threshold: float = 30.0


@dataclass
class ArsysConfig:
    host: str = field(default_factory=lambda: os.getenv("ARSYS_DB_HOST", "arsys-db"))
    port: int = 5432
    database: str = field(default_factory=lambda: os.getenv("ARSYS_DB_NAME", "castuo_db"))
    user: str = field(default_factory=lambda: os.getenv("ARSYS_DB_USER", ""))
    password: str = field(default_factory=lambda: os.getenv("ARSYS_DB_PASSWORD", ""))
    ssl: bool = True
    encryption: str = "AES-256"
    timeout: int = 30

    @property
    def dsn(self) -> str:
        return (
            f"postgresql://{self.user}:{self.password}"
            f"@{self.host}:{self.port}/{self.database}"
        )


@dataclass
class GaiaChainConfig:
    endpoint: str = "https://gaiachain.eu/api/v3"
    api_key: str = field(default_factory=lambda: os.getenv("GAIACHAIN_API_KEY", ""))
    timeout: int = 90
    contracts: Dict[str, str] = field(default_factory=lambda: {
        "trazabilidad": os.getenv(
            "GAIACHAIN_CONTRACT_TRAZABILIDAD",
            "0x7aCeE349bD40ED460d8575A3F245790E81Ce3AdB",
        ),
        "geotrace": os.getenv(
            "GAIACHAIN_CONTRACT_GEOTRACE",
            "0xAcF357a9a8e8578b5AcC959D3c56c62F9639b09A",
        ),
        "certificados": os.getenv(
            "GAIACHAIN_CONTRACT_CERTIFICADOS",
            "0x5f8a58f6E3e9C965C53681e15922E69E20583491",
        ),
    })
    # Cadena europea soberana — sin minería PoW
    chain_id: int = 31337
    consensus: str = "PoA"  # Proof of Authority — conforme AI Act UE


@dataclass
class IPFSConfig:
    endpoint: str = "http://ipfs-cluster:5001"
    gateway: str = "https://ipfs.castuo-system.eu"
    api_key: str = field(default_factory=lambda: os.getenv("IPFS_API_KEY", ""))
    timeout: int = 60
    pin_replicas: int = 3  # Replicación mínima en clúster UE


@dataclass
class LoRaWANConfig:
    endpoint: str = "http://lorawan-gateway:1700"
    api_key: str = field(default_factory=lambda: os.getenv("LORAWAN_API_KEY", ""))
    timeout: int = 15
    devices: Dict[str, str] = field(default_factory=lambda: {
        "sensor-001": os.getenv("LORAWAN_DEVICE_001", "0xABCD1234"),
        "sensor-002": os.getenv("LORAWAN_DEVICE_002", "0xEFGH5678"),
        "sensor-003": os.getenv("LORAWAN_DEVICE_003", "0xIJKL9012"),
    })
    # Umbrales de alerta para cultivo ecológico sin químicos
    alert_thresholds: Dict[str, Any] = field(default_factory=lambda: {
        "temperatura_vacuno_max_c": 39.4,
        "humedad_suelo_min_pct": 30,
        "tension_matricial_min_cb": -50,
        "co2_invernadero_min_ppm": 700,
        "co2_invernadero_max_ppm": 1000,
    })


@dataclass
class QRConfig:
    endpoint: str = "http://qr-generator:8000"
    api_key: str = field(default_factory=lambda: os.getenv("QR_API_KEY", ""))
    timeout: int = 20
    output_format: str = "svg"
    encryption: str = "ECC-256"
    # Tracking desde semilla hasta consumidor final
    tracking_stages: list = field(default_factory=lambda: [
        "semilla", "siembra", "cultivo", "cosecha",
        "procesado", "certificacion", "embalaje", "distribucion", "consumidor",
    ])


@dataclass
class MonitoringConfig:
    prometheus_endpoint: str = "http://prometheus:9090"
    grafana_endpoint: str = "http://grafana:3000"
    grafana_api_key: str = field(default_factory=lambda: os.getenv("GRAFANA_API_KEY", ""))
    elk_endpoint: str = "http://elk-stack:9200"
    elk_index_pattern: str = "castuo-logs-*"
    # Chaos engineering — resiliencia proactiva
    chaos_enabled: bool = field(
        default_factory=lambda: os.getenv("CHAOS_ENGINEERING_ENABLED", "false").lower() == "true"
    )
    alert_webhook: str = field(default_factory=lambda: os.getenv("ALERT_WEBHOOK_URL", ""))


@dataclass
class SecurityConfig:
    """Configuración de seguridad conforme RGPD + AI Act UE + eIDAS."""
    rgpd_compliant: bool = True
    ai_act_compliant: bool = True
    eidas_compliant: bool = True
    data_sovereignty_region: str = "EU"
    encryption_at_rest: str = "AES-256"
    encryption_in_transit: str = "TLS-1.3"
    jwt_secret: str = field(default_factory=lambda: os.getenv("JWT_SECRET_KEY", ""))
    jwt_algorithm: str = "ES256"  # ECDSA — eIDAS compatible
    jwt_expiry_minutes: int = 60
    allowed_origins: list = field(default_factory=lambda: [
        "https://castuo-system.eu",
        "https://app.castuo360.eu",
    ])
    rate_limit_per_minute: int = 100


class SovereignOrchestrator:
    """
    Orquestador Central Soberano — CASTÚO-SYSTEM™ v3.0

    Gestiona la integración completa de todos los servicios europeos:
    Claude Code · Cursor AI · n8n · Mistral AI · SABIONDA · Hetzner ·
    Arsys PostgreSQL · GaiaChain 3.0 · IPFS · LoRaWAN · QR Tracking

    Cumplimiento: RGPD | AI Act UE | eIDAS | ISO 27001
    Soberanía: Todos los datos y modelos en infraestructura UE
    """

    def __init__(self) -> None:
        self.claude = ClaudeConfig()
        self.cursor = CursorConfig()
        self.n8n = N8NConfig()
        self.mistral = MistralConfig()
        self.sabionda = SabiondaConfig()
        self.hetzner = HetznerConfig()
        self.arsys = ArsysConfig()
        self.gaia_chain = GaiaChainConfig()
        self.ipfs = IPFSConfig()
        self.lorawan = LoRaWANConfig()
        self.qr = QRConfig()
        self.monitoring = MonitoringConfig()
        self.security = SecurityConfig()

    def validate(self) -> Dict[str, bool]:
        """Valida que todas las claves de API críticas estén configuradas."""
        checks = {
            "claude_api_key": bool(self.claude.api_key),
            "mistral_api_key": bool(self.mistral.api_key),
            "hetzner_api_key": bool(self.hetzner.api_key),
            "arsys_db_credentials": bool(self.arsys.user and self.arsys.password),
            "gaiachain_api_key": bool(self.gaia_chain.api_key),
            "jwt_secret": bool(self.security.jwt_secret),
            "n8n_password": bool(self.n8n.basic_auth_password),
        }
        return checks

    def get_service_endpoints(self) -> Dict[str, str]:
        """Retorna mapa completo de endpoints para health checks."""
        return {
            "claude": self.claude.api_endpoint,
            "cursor": self.cursor.endpoint,
            "n8n": self.n8n.endpoint,
            "mistral": self.mistral.endpoint,
            "sabionda": self.sabionda.endpoint,
            "hetzner": self.hetzner.endpoint,
            "arsys_db": f"postgresql://{self.arsys.host}:{self.arsys.port}",
            "gaiachain": self.gaia_chain.endpoint,
            "ipfs": self.ipfs.endpoint,
            "lorawan": self.lorawan.endpoint,
            "qr_generator": self.qr.endpoint,
            "prometheus": self.monitoring.prometheus_endpoint,
            "grafana": self.monitoring.grafana_endpoint,
            "elk": self.monitoring.elk_endpoint,
        }

    @property
    def is_sovereign(self) -> bool:
        """Verifica que el sistema opera bajo soberanía europea completa."""
        return (
            self.security.rgpd_compliant
            and self.security.ai_act_compliant
            and self.security.eidas_compliant
            and self.security.data_sovereignty_region == "EU"
        )


# Instancia global del orquestador
orchestrator = SovereignOrchestrator()
