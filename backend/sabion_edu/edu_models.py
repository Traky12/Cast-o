# backend/sabion_edu/edu_models.py
"""Modelos protocolo educativo v5.0 — Niveles TRL1-9, microcredenciales blockchain."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List

NIVELES = {
    "TRL1": 1, "TRL2": 2, "TRL3": 3, "TRL4": 4, "TRL5": 5,
    "TRL6": 6, "TRL7": 7, "TRL8": 8, "TRL9": 9,
}
HABILIDADES_POR_NIVEL: Dict[int, List[str]] = {
    1: ["AnytypeP2P", "DockerBasico", "AgentesIntro"],
    2: ["AnytypeP2P", "DockerFed", "Kyber1024", "Consenso2/3"],
    3: ["MerkleTree", "IPFS", "SmartGDPR", "ByzantineFT"],
    4: ["MLOracle", "VaultPQC", "SabiondaOrchestrate"],
    5: ["CTAEXDemo", "Federacion3Nodos"],
    6: ["TRL8Production", "CertificacionISO"],
    7: ["GodMode", "Omega2040", "50Nodos"],
    8: ["Revenue50M", "Estrategia2040"],
    9: ["ADMIN_EXCLUSIVO", "Kyber2048"],
}
CERT_NAMES: Dict[int, str] = {
    1: "TRL1_Fundamentos",
    2: "TRL2_Tecnico_Federado",
    3: "TRL3_Auditor_Blockchain",
    4: "TRL4_Especialista",
    5: "TRL5_Especialista_CTAEX",
    6: "TRL6_Especialista_TRL8",
    7: "TRL7_Omega_Candidato",
    8: "TRL8_Omega_Admin",
    9: "TRL9_ADMIN_2040",
}
REVENUE_PER_CERT: Dict[int, int] = {
    1: 5_000, 2: 5_000, 3: 5_000,
    4: 15_000, 5: 15_000, 6: 15_000,
    7: 50_000, 8: 50_000, 9: 50_000,
}

STUDENTS: Dict[str, Dict[str, Any]] = {}
CERTIFICATES: List[Dict[str, Any]] = []
