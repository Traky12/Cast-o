# -*- coding: utf-8 -*-
"""Agentes autónomos CASTÚO: Sabionda-Omega, CodeAgent, LexCheck-UE, YieldMaster, DocuBot-2040."""
from backend.agents_autonomous.sabionda_omega import validar_mejora
from backend.agents_autonomous.lex_check_ue import auditar_cumplimiento
from backend.agents_autonomous.yield_master import analizar_yield
from backend.agents_autonomous.code_agent_autonomous import AutonomousImprover

__all__ = [
    "validar_mejora",
    "auditar_cumplimiento",
    "analizar_yield",
    "AutonomousImprover",
]

try:
    from backend.agents_autonomous.docubot_2040 import DocuBot2040
    __all__.append("DocuBot2040")
except ImportError:
    DocuBot2040 = None

try:
    from backend.agents_autonomous.invoice_bot import InvoiceBot
    __all__.append("InvoiceBot")
except ImportError:
    InvoiceBot = None
try:
    from backend.agents_autonomous.payment_gateway import PaymentGateway
    __all__.append("PaymentGateway")
except ImportError:
    PaymentGateway = None
try:
    from backend.agents_autonomous.aeat_bot import AEATBot
    __all__.append("AEATBot")
except ImportError:
    AEATBot = None
try:
    from backend.agents_autonomous.market_bot import MarketBot
    __all__.append("MarketBot")
except ImportError:
    MarketBot = None
try:
    from backend.agents_autonomous.stripe_integration import StripeIntegration
    __all__.append("StripeIntegration")
except ImportError:
    StripeIntegration = None
try:
    from backend.agents_autonomous.nft_marketplace import NFTMarketplace
    __all__.append("NFTMarketplace")
except ImportError:
    NFTMarketplace = None

try:
    from backend.agents_autonomous.subscription_manager import SubscriptionManager
    __all__.append("SubscriptionManager")
except ImportError:
    SubscriptionManager = None
try:
    from backend.agents_autonomous.data_marketplace import DataMarketplace
    __all__.append("DataMarketplace")
except ImportError:
    DataMarketplace = None
try:
    from backend.agents_autonomous.automatic_billing import AutomaticBilling
    __all__.append("AutomaticBilling")
except ImportError:
    AutomaticBilling = None
try:
    from backend.agents_autonomous.nft_monetization import NFTMonetization
    __all__.append("NFTMonetization")
except ImportError:
    NFTMonetization = None
try:
    from backend.agents_autonomous.revenue_dashboard import RevenueDashboard
    __all__.append("RevenueDashboard")
except ImportError:
    RevenueDashboard = None
