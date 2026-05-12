# -*- coding: utf-8 -*-
"""Módulos legales: sellos eIDAS 2, GDPR, AI Act 2024, certificados soberanos, GaiaChain."""
from backend.legal.gaiachain_seal import GaiaChainSeal
from backend.legal.gdpr_compliance import GDPRCompliance
from backend.legal.ai_act_compliance import AIActCompliance
from backend.legal.certificate_generator import SovereignCertificateGenerator

__all__ = ["GaiaChainSeal", "GDPRCompliance", "AIActCompliance", "SovereignCertificateGenerator"]
