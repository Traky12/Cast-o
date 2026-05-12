# -*- coding: utf-8 -*-
"""Generación de contratos legales (BioCoin, suministro) con validación LexCheck-UE y GaiaChain."""
from __future__ import annotations

import json
import logging
import os
import subprocess
from datetime import datetime, timezone
from typing import Any, Dict, List

from backend.agents_autonomous.lex_check_ue import auditar_cumplimiento

logger = logging.getLogger(__name__)

_GAIACHAIN_CLI = os.getenv("GAIACHAIN_CLI", "/usr/local/bin/gaiachain")


def generate_contract(
    contract_type: str,
    parties: List[str],
    terms: List[Dict[str, str]],
    jurisdiction: str = "EU",
) -> Dict[str, Any]:
    """
    Genera un contrato (stub markdown) y valida con LexCheck-UE; opcional registro GaiaChain.
    """
    contract_text = _build_contract_markdown(contract_type, parties, terms, jurisdiction)
    mejora = {
        "código": contract_text,
        "métrica": "legal",
        "antes": 0,
        "después": 1,
        "cambios": [t.get("clause", "") for t in terms],
    }
    auditoria = auditar_cumplimiento(mejora)
    tx_hash = _registrar_contrato_gaiachain(contract_type, parties, terms, contract_text)
    return {
        "contract_type": contract_type,
        "parties": parties,
        "terms": terms,
        "jurisdiction": jurisdiction,
        "contract_markdown": contract_text,
        "lexcheck_aprobado": auditoria.get("aprobado"),
        "normativas": auditoria.get("normativas", []),
        "issues": auditoria.get("issues", []),
        "gaiachain_tx": tx_hash,
    }


def _build_contract_markdown(
    contract_type: str, parties: List[str], terms: List[Dict[str, str]], jurisdiction: str
) -> str:
    lines = [
        f"# Contrato {contract_type}",
        f"**Partes**: {' y '.join(parties)}",
        f"**Jurisdicción**: {jurisdiction}",
        f"**Fecha**: {datetime.now(timezone.utc).strftime('%Y-%m-%d')}",
        "",
        "## Cláusulas",
    ]
    for t in terms:
        lines.append(f"- **{t.get('clause', 'Cláusula')}**: {t.get('requirement', '')} ({t.get('normativa', '')})")
    lines.append("")
    lines.append("---")
    lines.append("Trazabilidad: GaiaChain + eIDAS. Datos anonimizados según GDPR Art. 25.")
    return "\n".join(lines)


def _registrar_contrato_gaiachain(
    contract_type: str, parties: List[str], terms: List[Dict[str, str]], contract_text: str
) -> str:
    if not os.path.isfile(_GAIACHAIN_CLI):
        return "gaiachain-no-cli"
    try:
        data = {
            "type": "legal_contract",
            "contract_type": contract_type,
            "parties": parties,
            "terms": terms,
            "hash_preview": contract_text[:200],
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        r = subprocess.run(
            [_GAIACHAIN_CLI, "record", "--type", "legal_contract", "--data", json.dumps(data)],
            capture_output=True,
            text=True,
            timeout=10,
        )
        return (r.stdout or "").strip() or "ok" if r.returncode == 0 else f"Error: {r.stderr}"
    except Exception as e:
        return f"Error: {e}"
