# -*- coding: utf-8 -*-
"""AEATBot: declaraciones de IVA (modelo 303) y registro en GaiaChain (Orden HFP/417/2022)."""
from __future__ import annotations

import hashlib
import json
import logging
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

_GAIACHAIN_CLI = os.getenv("GAIACHAIN_CLI", os.getenv("GAIA_CHAIN_CLI", "/usr/local/bin/gaiachain"))
_REPO_ROOT = Path(__file__).resolve().parents[2]
_AEAT_DIR = _REPO_ROOT / "aeat"


class AEATBot:
    """Genera declaración de IVA (303) y XML para AEAT; registro en GaiaChain."""

    def __init__(self) -> None:
        self.gaiachain_cli = _GAIACHAIN_CLI
        self.company_data = {
            "cif": os.getenv("COMPANY_CIF", "B12345678"),
            "nombre": os.getenv("COMPANY_NAME", "CASTÚO-SYSTEM S.L."),
            "regimen_iva": "general",
            "obligado_sii": True,
        }

    def generate_iva_declaration(self, month: int, year: int) -> Dict[str, Any]:
        """Genera declaración de IVA para el periodo (modelo 303)."""
        invoices = self._query_invoices(month, year)
        declaration = self._calculate_iva(invoices, month, year)
        _AEAT_DIR.mkdir(parents=True, exist_ok=True)
        xml_path = self._generate_xml_303(declaration)
        tx_hash = self._register_declaration_in_gaiachain(declaration, xml_path)
        return {
            "status": "success",
            "declaration": declaration,
            "xml_path": str(xml_path),
            "gaiachain_tx": tx_hash,
        }

    def _query_invoices(self, month: int, year: int) -> List[Dict[str, Any]]:
        if not os.path.isfile(self.gaiachain_cli):
            return []
        try:
            r = subprocess.run(
                [
                    self.gaiachain_cli, "query", "--type", "invoice",
                    "--start", f"{year}-{month:02d}-01",
                    "--end", f"{year}-{month:02d}-31",
                ],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if r.returncode == 0 and r.stdout.strip():
                return json.loads(r.stdout) if isinstance(r.stdout, str) else []
        except Exception as e:
            logger.warning("GaiaChain query invoices: %s", e)
        return []

    def _calculate_iva(self, invoices: List[Dict[str, Any]], month: int, year: int) -> Dict[str, Any]:
        bases = {
            "general": {"base": 0.0, "cuota": 0.0, "tipo": 21},
            "reducido": {"base": 0.0, "cuota": 0.0, "tipo": 10},
            "superreducido": {"base": 0.0, "cuota": 0.0, "tipo": 4},
        }
        for inv in invoices:
            data = inv.get("data", inv) if isinstance(inv, dict) else {}
            productos = data.get("productos", [])
            if not productos:
                key = "general"
            else:
                tipo = (productos[0].get("tipo") or "").lower()
                if "cannabis" in tipo:
                    key = "superreducido"
                elif "microgreen" in tipo:
                    key = "reducido"
                else:
                    key = "general"
            bases[key]["base"] += float(data.get("subtotal", 0))
            bases[key]["cuota"] += float(data.get("iva", 0))
        total_base = sum(b["base"] for b in bases.values())
        total_cuota = sum(b["cuota"] for b in bases.values())
        return {
            "periodo": f"{month}/{year}",
            "obligado": self.company_data,
            "bases_imponibles": bases,
            "total_base": total_base,
            "total_cuota": total_cuota,
            "resultado": total_cuota,
            "normativa": "Orden HFP/417/2022 (Modelo 303)",
        }

    def _generate_xml_303(self, declaration: Dict[str, Any]) -> Path:
        per = declaration["periodo"].replace("/", "")
        path = _AEAT_DIR / f"303_{per}.xml"
        bi = declaration["bases_imponibles"]
        xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Modelo303>
    <Cabecera>
        <Ejercicio>{declaration['periodo'].split('/')[1]}</Ejercicio>
        <Periodo>{declaration['periodo'].split('/')[0]}</Periodo>
        <NIF>{declaration['obligado']['cif']}</NIF>
        <Nombre>{declaration['obligado']['nombre']}</Nombre>
    </Cabecera>
    <Detalle>
        <BaseImponible tipo="general">
            <Importe>{bi['general']['base']:.2f}</Importe>
            <Cuota>{bi['general']['cuota']:.2f}</Cuota>
        </BaseImponible>
        <BaseImponible tipo="reducido">
            <Importe>{bi['reducido']['base']:.2f}</Importe>
            <Cuota>{bi['reducido']['cuota']:.2f}</Cuota>
        </BaseImponible>
        <BaseImponible tipo="superreducido">
            <Importe>{bi['superreducido']['base']:.2f}</Importe>
            <Cuota>{bi['superreducido']['cuota']:.2f}</Cuota>
        </BaseImponible>
        <Total>
            <Base>{declaration['total_base']:.2f}</Base>
            <Cuota>{declaration['total_cuota']:.2f}</Cuota>
            <Resultado>{declaration['resultado']:.2f}</Resultado>
        </Total>
    </Detalle>
    <Pie>
        <Normativa>Orden HFP/417/2022</Normativa>
        <FechaGeneracion>{datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S')}</FechaGeneracion>
    </Pie>
</Modelo303>"""
        path.write_text(xml, encoding="utf-8")
        return path

    def _register_declaration_in_gaiachain(self, declaration: Dict[str, Any], xml_path: Path) -> str:
        if not os.path.isfile(self.gaiachain_cli):
            return "gaiachain-no-cli"
        xml_hash = ""
        if xml_path.is_file():
            xml_hash = hashlib.sha256(xml_path.read_bytes()).hexdigest()
        tx_data = {
            "type": "aeat_declaration",
            "data": {
                **declaration,
                "xml_hash": xml_hash,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        }
        try:
            r = subprocess.run(
                [self.gaiachain_cli, "record", "--type", "aeat_declaration", "--data", json.dumps(tx_data)],
                capture_output=True,
                text=True,
                timeout=10,
            )
            return (r.stdout or "").strip() or "ok" if r.returncode == 0 else f"Error: {r.stderr}"
        except Exception as e:
            return f"Error: {e}"

    def submit_to_aeat(self, xml_path: str) -> Dict[str, Any]:
        """Simula envío a AEAT (en producción integrar SII o gestor)."""
        return {
            "status": "submitted",
            "message": f"Declaracion {xml_path} enviada a la AEAT (simulado)",
            "reference": f"AEAT-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}",
        }

    def generate_annual_summary(self, year: int) -> Dict[str, Any]:
        """Genera resumen anual (modelo 390) para la AEAT a partir de facturas en GaiaChain."""
        invoices = self._query_invoices_by_year(year)
        summary = {
            "year": year,
            "trimestres": [{"base": 0.0, "cuota": 0.0} for _ in range(4)],
            "totales": {"general": {"base": 0.0, "cuota": 0.0}, "reducido": {"base": 0.0, "cuota": 0.0}, "superreducido": {"base": 0.0, "cuota": 0.0}},
        }
        for inv in invoices:
            data = inv.get("data", inv) if isinstance(inv, dict) else {}
            month = int((data.get("fecha") or "2026-01").split("-")[1])
            q = min(4, max(1, (month - 1) // 3 + 1))
            summary["trimestres"][q - 1]["base"] += float(data.get("subtotal", 0))
            summary["trimestres"][q - 1]["cuota"] += float(data.get("iva", 0))
            productos = data.get("productos", [])
            tipo = (productos[0].get("tipo") or "").lower() if productos else ""
            if "cannabis" in tipo:
                key = "superreducido"
            elif "microgreen" in tipo or "servicio" in tipo:
                key = "reducido"
            else:
                key = "general"
            summary["totales"][key]["base"] += float(data.get("subtotal", 0))
            summary["totales"][key]["cuota"] += float(data.get("iva", 0))
        _AEAT_DIR.mkdir(parents=True, exist_ok=True)
        xml_path = self._generate_xml_390(summary)
        xml_hash = hashlib.sha256(xml_path.read_bytes()).hexdigest() if (xml_path and xml_path.is_file()) else ""
        gaia_tx = self._register_390_gaiachain(year, summary, xml_hash)
        return {"status": "success", "summary": summary, "xml_path": str(xml_path), "gaiachain_tx": gaia_tx}

    def _query_invoices_by_year(self, year: int) -> List[Dict[str, Any]]:
        if not os.path.isfile(self.gaiachain_cli):
            return []
        try:
            r = subprocess.run(
                [self.gaiachain_cli, "query", "--type", "invoice", "--start", f"{year}-01-01", "--end", f"{year}-12-31"],
                capture_output=True, text=True, timeout=15,
            )
            if r.returncode == 0 and r.stdout.strip():
                out = json.loads(r.stdout)
                return out if isinstance(out, list) else [out]
        except Exception as e:
            logger.warning("GaiaChain query invoices year: %s", e)
        return []

    def _generate_xml_390(self, summary: Dict[str, Any]) -> Path:
        path = _AEAT_DIR / f"390_{summary['year']}.xml"
        t = summary["trimestres"]
        tot = summary["totales"]
        xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Modelo390>
    <Cabecera>
        <Ejercicio>{summary['year']}</Ejercicio>
        <NIF>{self.company_data['cif']}</NIF>
        <Nombre>{self.company_data['nombre']}</Nombre>
    </Cabecera>
    <ResumenAnual>
        <Operaciones>
            <Tipo>General</Tipo>
            <BaseImponible>{tot['general']['base']:.2f}</BaseImponible>
            <Cuota>{tot['general']['cuota']:.2f}</Cuota>
        </Operaciones>
        <Operaciones>
            <Tipo>Reducido</Tipo>
            <BaseImponible>{tot['reducido']['base']:.2f}</BaseImponible>
            <Cuota>{tot['reducido']['cuota']:.2f}</Cuota>
        </Operaciones>
        <Operaciones>
            <Tipo>Superreducido</Tipo>
            <BaseImponible>{tot['superreducido']['base']:.2f}</BaseImponible>
            <Cuota>{tot['superreducido']['cuota']:.2f}</Cuota>
        </Operaciones>
    </ResumenAnual>
    <DesgloseTrimestral>
        <Trimestre numero="1"><BaseImponible>{t[0]['base']:.2f}</BaseImponible><Cuota>{t[0]['cuota']:.2f}</Cuota></Trimestre>
        <Trimestre numero="2"><BaseImponible>{t[1]['base']:.2f}</BaseImponible><Cuota>{t[1]['cuota']:.2f}</Cuota></Trimestre>
        <Trimestre numero="3"><BaseImponible>{t[2]['base']:.2f}</BaseImponible><Cuota>{t[2]['cuota']:.2f}</Cuota></Trimestre>
        <Trimestre numero="4"><BaseImponible>{t[3]['base']:.2f}</BaseImponible><Cuota>{t[3]['cuota']:.2f}</Cuota></Trimestre>
    </DesgloseTrimestral>
    <Pie>
        <Normativa>Orden HFP/112/2023 (Modelo 390)</Normativa>
        <FechaGeneracion>{datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S')}</FechaGeneracion>
    </Pie>
</Modelo390>"""
        path.write_text(xml, encoding="utf-8")
        return path

    def _register_390_gaiachain(self, year: int, summary: Dict[str, Any], xml_hash: str) -> str:
        if not os.path.isfile(self.gaiachain_cli):
            return "gaiachain-no-cli"
        payload = {"year": year, "summary": summary, "xml_hash": xml_hash, "timestamp": datetime.now(timezone.utc).isoformat()}
        try:
            r = subprocess.run(
                [self.gaiachain_cli, "record", "--type", "aeat_390", "--data", json.dumps(payload)],
                capture_output=True, text=True, timeout=10,
            )
            return (r.stdout or "").strip() or "ok" if r.returncode == 0 else f"Error: {r.stderr}"
        except Exception as e:
            return f"Error: {e}"

    def submit_annual_summary(self, xml_path: str) -> Dict[str, Any]:
        """Simula envío del resumen anual (390) a la AEAT."""
        return {
            "status": "submitted",
            "message": f"Resumen anual {xml_path} enviado a la AEAT (simulado)",
            "reference": f"AEAT-390-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
