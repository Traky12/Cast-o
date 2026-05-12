# -*- coding: utf-8 -*-
from .drones import router as drones_router
from .cameras import router as cameras_router
from .sensors import router as sensors_router
from .riego import router as riego_router
from .energia import router as energia_router
from .chatbot import router as chatbot_router
from .voice import router as voice_router
from .notifications import router as notifications_router
from .robotica import router as robotica_router
from .blockchain import router as blockchain_router
from .blockchain_gaia import router as blockchain_gaia_router
from .cannabis import router as cannabis_router
from .microgreens import router as microgreens_router
from .iot import router as iot_router
from .ue_compliance import router as ue_compliance_router
from .lims_sync import router as lims_sync_router
from .reports import router as reports_router
from .materiales import router as materiales_router
from .offline import router as offline_router
from .extrusora import router as extrusora_router
from .ia import router as ia_router
from .ctaex import router as ctaex_router
from .orchestrator import router as orchestrator_router
from .agents import router as agents_router
from .pro_accounts import router as pro_accounts_router
from .asia import router as asia_router
from .canada import router as canada_router
from .cooperativas import router as cooperativas_router
from .hidroponia import router as hidroponia_router
from .nft import router as nft_router
from .billing import router as billing_router
from .alertas import router as alertas_router
from .agri_sense_router import router as agri_sense_router
from .traceability_governance import router as traceability_governance_router
from .agents_autonomous import router as agents_autonomous_router
from .aemps_webhooks import router as aemps_webhooks_router
from .hydro_remote import router as hydro_remote_router
from .thc import router as thc_router
from .hydroponics_saas import router as hydroponics_saas_router
from .ai_hydroponics_saas import router as ai_hydroponics_saas_router
from .agrovoltaic_field import router as agrovoltaic_field_router
from .sabionda_workspace import router as sabionda_workspace_router
from .langgraph_castuo import router as langgraph_castuo_router
from . import water_ctaex

water_ctaex_router = water_ctaex.water_ctaex_router

__all__ = [
    "drones_router",
    "cameras_router",
    "sensors_router",
    "riego_router",
    "energia_router",
    "chatbot_router",
    "voice_router",
    "notifications_router",
    "robotica_router",
    "blockchain_router",
    "blockchain_gaia_router",
    "cannabis_router",
    "microgreens_router",
    "iot_router",
    "ue_compliance_router",
    "lims_sync_router",
    "reports_router",
    "materiales_router",
    "offline_router",
    "extrusora_router",
    "ia_router",
    "ctaex_router",
    "orchestrator_router",
    "agents_router",
    "pro_accounts_router",
    "asia_router",
    "canada_router",
    "cooperativas_router",
    "hidroponia_router",
    "nft_router",
    "billing_router",
    "alertas_router",
    "agri_sense_router",
    "traceability_governance_router",
    "agents_autonomous_router",
    "aemps_webhooks_router",
    "hydro_remote_router",
    "thc_router",
    "hydroponics_saas_router",
    "ai_hydroponics_saas_router",
    "agrovoltaic_field_router",
    "sabionda_workspace_router",
    "langgraph_castuo_router",
    "water_ctaex",
    "water_ctaex_router",
]
