# -*- coding: utf-8 -*-
"""InvoiceBot: generación de facturas (Ley 37/1992 IVA, Reglamento UE 2021/1153) y registro en GaiaChain."""
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
_INVOICES_DIR = _REPO_ROOT / "invoices"

try:
    from backend.database.local_db import local_db
except Exception:
    local_db = None

try:
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas
    _REPORTLAB = True
except ImportError:
    _REPORTLAB = False

IVA_RATES = {
    "cannabis_medicinal": 4,
    "microgreens": 10,
    "flores_comestibles": 21,
    "servicios_agronomicos": 21,
}


class InvoiceBot:
    """Genera facturas válidas, calcula IVA por tipo de producto y registra en GaiaChain."""

    def __init__(self) -> None:
        self.gaiachain_cli = _GAIACHAIN_CLI
        self.company_data = {
            "nombre": os.getenv("COMPANY_NAME", "CASTÚO-SYSTEM S.L."),
            "cif": os.getenv("COMPANY_CIF", "B12345678"),
            "direccion": os.getenv("COMPANY_ADDRESS", "Pol. Ind. La Dehesa, Cáceres"),
            "email": os.getenv("COMPANY_EMAIL", "facturacion@castuo-system.com"),
            "iban": os.getenv("COMPANY_IBAN", "ESXX 1234 5678 9012 3456 7890"),
        }

    def generate_invoice(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Genera factura: valida cliente, calcula IVA, genera PDF (o TXT si no hay ReportLab), registra en GaiaChain.
        """
        if not self._validate_client_data(order_data.get("cliente", {})):
            return {"status": "error", "reason": "Datos del cliente no válidos (GDPR): nombre, cif_nif, direccion, email"}

        invoice_data = self._calculate_taxes(order_data)
        _INVOICES_DIR.mkdir(parents=True, exist_ok=True)
        pdf_path = self._generate_pdf(invoice_data)
        if not pdf_path:
            pdf_path = self._generate_txt_invoice(invoice_data)
        hash_pdf = self._generate_pdf_hash(pdf_path) if os.path.isfile(pdf_path) else ""
        tx_hash = self._register_in_gaiachain(invoice_data, hash_pdf)
        if tx_hash and tx_hash.startswith("http"):
            qr_code = tx_hash
        else:
            qr_code = f"https://gaiachain.castuo-system.com/tx/{tx_hash}" if tx_hash else ""

        if local_db:
            try:
                local_db.log_invoice(
                    {
                        "invoice_data": {**invoice_data, "pdf_hash": hash_pdf},
                        "pdf_path": str(pdf_path),
                        "gaiachain_tx": tx_hash if isinstance(tx_hash, str) else None,
                    }
                )
            except Exception:
                pass

        return {
            "status": "success",
            "invoice": invoice_data,
            "pdf_path": str(pdf_path),
            "gaiachain_tx": tx_hash or "gaiachain-no-cli",
            "qr_code": qr_code,
        }

    PLANS = {
        "basic": {"price": 99.99, "analyses": 5, "frequency": "monthly"},
        "premium": {"price": 299.99, "analyses": 20, "frequency": "monthly"},
        "enterprise": {"price": 999.99, "analyses": "unlimited", "frequency": "monthly"},
    }

    def create_subscription(self, client_data: Dict[str, Any], plan: str) -> Dict[str, Any]:
        """Crea suscripción recurrente (basic/premium/enterprise), genera factura y registra en GaiaChain."""
        if plan not in self.PLANS:
            return {"status": "error", "reason": "Plan no valido (basic, premium, enterprise)"}
        if not self._validate_client_data(client_data):
            return {"status": "error", "reason": "Datos del cliente no validos"}
        p = self.PLANS[plan]
        order_data = {
            "cliente": client_data,
            "productos": [{
                "nombre": f"Suscripcion {plan.capitalize()} - Analisis de Cultivos",
                "tipo": "servicios_agronomicos",
                "cantidad": 1,
                "precio_unitario": p["price"],
            }],
            "notas": f"Suscripcion automatica para {p['analyses']} analisis/mes",
            "tipo": "subscription",
        }
        result = self.generate_invoice(order_data)
        if result.get("status") != "success":
            return result
        start_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        subscription_id = f"SUB-{client_data.get('cif_nif', '')[:8]}-{plan}-{start_date.replace('-', '')}"
        subscription_data = {
            "subscription_id": subscription_id,
            "client_id": client_data.get("cif_nif"),
            "client_name": client_data.get("nombre"),
            "plan": plan,
            "start_date": start_date,
            "frequency": p["frequency"],
            "status": "active",
            "invoice_id": result["invoice"]["numero_factura"],
            "gaiachain_tx": result.get("gaiachain_tx"),
        }
        tx_sub = self._register_in_gaiachain_subscription(subscription_data)
        subscription_data["gaiachain_tx"] = tx_sub or subscription_data.get("gaiachain_tx")
        return {
            "status": "success",
            "subscription": subscription_data,
            "invoice": result["invoice"],
            "pdf_path": result.get("pdf_path"),
            "gaiachain_tx": result.get("gaiachain_tx"),
        }

    def generate_recurring_invoice(self, subscription_id: str) -> Dict[str, Any]:
        """Genera factura recurrente para una suscripción (consulta GaiaChain o stub)."""
        subscription = self._query_subscription(subscription_id)
        if not subscription:
            return {"status": "error", "reason": "No se encontro la suscripcion"}
        prices = {"basic": 99.99, "premium": 299.99, "enterprise": 999.99}
        order_data = {
            "cliente": {
                "nombre": subscription.get("client_name", "Cliente"),
                "cif_nif": subscription.get("client_id", ""),
                "direccion": subscription.get("direccion", "N/A"),
                "email": subscription.get("email", "cliente@example.com"),
            },
            "productos": [{
                "nombre": f"Renovacion Suscripcion {subscription.get('plan', '').capitalize()}",
                "tipo": "servicios_agronomicos",
                "cantidad": 1,
                "precio_unitario": prices.get(subscription.get("plan", "basic"), 99.99),
            }],
            "notas": f"Factura recurrente para suscripcion {subscription_id}",
            "tipo": "recurring",
        }
        return self.generate_invoice(order_data)

    def generate_credit_note(self, invoice_id: str, reason: str) -> Dict[str, Any]:
        """Genera nota de credito para una factura (consulta GaiaChain o stub con totales negativos)."""
        original = self._query_invoice(invoice_id)
        if not original:
            return {"status": "error", "reason": "No se encontro la factura"}
        data = original.get("data", original)
        productos = data.get("productos", [])
        if not productos:
            productos = [{"nombre": "Concepto anulado", "cantidad": 1, "precio_unitario": -float(data.get("total", 0)), "iva": 21, "subtotal": -float(data.get("subtotal", 0)), "iva_amount": -float(data.get("iva", 0))}]
        else:
            productos = [{**p, "precio_unitario": -abs(p.get("precio_unitario", 0)), "subtotal": -abs(p.get("subtotal", 0)), "iva_amount": -abs(p.get("iva_amount", 0))} for p in productos]
        subtotal = sum(p.get("subtotal", 0) for p in productos)
        total_iva = sum(p.get("iva_amount", 0) for p in productos)
        total = subtotal + total_iva
        credit_note_data = {
            "numero_factura": f"NC-{invoice_id}",
            "cliente": data.get("cliente") if isinstance(data.get("cliente"), dict) else {"nombre": "Cliente", "cif_nif": data.get("cliente", "N/A"), "direccion": "N/A", "email": "noreply@castuo-system.com"},
            "productos": productos,
            "subtotal": subtotal,
            "iva": total_iva,
            "total": total,
            "fecha": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "notas": f"Nota de credito: {reason}",
            "factura_original": invoice_id,
            "empresa": self.company_data,
            "normativa": "Ley 37/1992 (IVA), Reglamento UE 2021/1153",
        }
        _INVOICES_DIR.mkdir(parents=True, exist_ok=True)
        pdf_path = self._generate_pdf(credit_note_data, credit_note=True)
        if not pdf_path:
            pdf_path = self._generate_txt_invoice(credit_note_data, credit_note=True)
        hash_pdf = self._generate_pdf_hash(pdf_path) if os.path.isfile(pdf_path) else ""
        tx_hash = self._register_credit_note_gaiachain(credit_note_data, invoice_id, reason, hash_pdf)
        return {"status": "success", "credit_note": credit_note_data, "pdf_path": str(pdf_path), "original_invoice": invoice_id, "gaiachain_tx": tx_hash}

    def _query_subscription(self, subscription_id: str) -> Dict[str, Any] | None:
        if not os.path.isfile(self.gaiachain_cli):
            return {"subscription_id": subscription_id, "client_id": "stub", "client_name": "Cliente", "plan": "basic", "frequency": "monthly"}
        try:
            r = subprocess.run(
                [self.gaiachain_cli, "query", "--type", "subscription", "--subscription_id", subscription_id],
                capture_output=True, text=True, timeout=10,
            )
            if r.returncode == 0 and r.stdout.strip():
                out = json.loads(r.stdout)
                return out.get("data", out)
        except Exception:
            pass
        return None

    def _query_invoice(self, invoice_id: str) -> Dict[str, Any] | None:
        if not os.path.isfile(self.gaiachain_cli):
            return {"data": {"numero_factura": invoice_id, "cliente": {"nombre": "Cliente", "cif_nif": "N/A", "direccion": "N/A", "email": "noreply@castuo-system.com"}, "productos": [{"nombre": "Factura stub", "cantidad": 1, "precio_unitario": 100, "subtotal": 100, "iva_amount": 21, "iva": 21}], "subtotal": 100, "iva": 21, "total": 121}}
        try:
            r = subprocess.run(
                [self.gaiachain_cli, "query", "--type", "invoice", "--invoice_id", invoice_id],
                capture_output=True, text=True, timeout=10,
            )
            if r.returncode == 0 and r.stdout.strip():
                return json.loads(r.stdout)
        except Exception:
            pass
        return None

    def _register_in_gaiachain_subscription(self, data: Dict[str, Any]) -> str:
        if not os.path.isfile(self.gaiachain_cli):
            return "gaiachain-no-cli"
        try:
            r = subprocess.run(
                [self.gaiachain_cli, "record", "--type", "subscription", "--data", json.dumps(data)],
                capture_output=True, text=True, timeout=10,
            )
            return (r.stdout or "").strip() or "ok" if r.returncode == 0 else f"Error: {r.stderr}"
        except Exception as e:
            return f"Error: {e}"

    def _register_credit_note_gaiachain(self, credit_note_data: Dict[str, Any], original_invoice: str, reason: str, hash_pdf: str) -> str:
        if not os.path.isfile(self.gaiachain_cli):
            return "gaiachain-no-cli"
        payload = {"credit_note_id": credit_note_data["numero_factura"], "original_invoice": original_invoice, "reason": reason, "pdf_hash": hash_pdf, "timestamp": datetime.now(timezone.utc).isoformat()}
        try:
            r = subprocess.run(
                [self.gaiachain_cli, "record", "--type", "credit_note", "--data", json.dumps(payload)],
                capture_output=True, text=True, timeout=10,
            )
            return (r.stdout or "").strip() or "ok" if r.returncode == 0 else f"Error: {r.stderr}"
        except Exception as e:
            return f"Error: {e}"

    def get_invoices(self, period: str = "month") -> List[Dict[str, Any]]:
        """Consulta facturas en GaiaChain para el periodo (stub si no hay CLI)."""
        if not os.path.isfile(self.gaiachain_cli):
            return []
        try:
            end = datetime.now(timezone.utc)
            start = end.replace(day=1) if period == "month" else end.replace(month=1, day=1)
            r = subprocess.run(
                [self.gaiachain_cli, "query", "--type", "invoice", "--start", start.strftime("%Y-%m-%d"), "--end", end.strftime("%Y-%m-%d")],
                capture_output=True, text=True, timeout=10,
            )
            if r.returncode == 0 and r.stdout.strip():
                out = json.loads(r.stdout)
                return out if isinstance(out, list) else [out]
        except Exception:
            pass
        return []

    def _validate_client_data(self, client: Dict[str, Any]) -> bool:
        required = ["nombre", "cif_nif", "direccion", "email"]
        return all(client.get(field) for field in required)

    def _calculate_taxes(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        productos: List[Dict[str, Any]] = []
        for item in order_data.get("productos", []):
            iva_rate = IVA_RATES.get(item.get("tipo", ""), 21)
            subtotal = item.get("cantidad", 0) * item.get("precio_unitario", 0)
            iva_amount = subtotal * iva_rate / 100
            productos.append({
                **item,
                "iva": iva_rate,
                "subtotal": subtotal,
                "iva_amount": iva_amount,
            })
        subtotal = sum(p["subtotal"] for p in productos)
        total_iva = sum(p["iva_amount"] for p in productos)
        total = subtotal + total_iva
        numero_factura = f"FACT-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}"
        return {
            **order_data,
            "productos": productos,
            "subtotal": subtotal,
            "iva": total_iva,
            "total": total,
            "fecha": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "numero_factura": numero_factura,
            "empresa": self.company_data,
            "normativa": "Ley 37/1992 (IVA), Reglamento UE 2021/1153 (Facturación Electrónica)",
        }

    def _generate_pdf(self, invoice_data: Dict[str, Any], credit_note: bool = False) -> str:
        if not _REPORTLAB:
            return ""
        title = "NOTA DE CREDITO" if credit_note else "FACTURA"
        prefix = "NC" if credit_note else "FACT"
        path = _INVOICES_DIR / f"{prefix}_{invoice_data['numero_factura'].replace('/', '-')}.pdf"
        try:
            c = canvas.Canvas(str(path), pagesize=letter)
            c.setFont("Helvetica-Bold", 16)
            c.drawString(100, 750, title)
            c.setFont("Helvetica", 12)
            c.drawString(100, 730, f"Numero: {invoice_data['numero_factura']}")
            c.drawString(100, 710, f"Fecha: {invoice_data['fecha']}")
            c.drawString(100, 680, f"Emisor: {self.company_data['nombre']}")
            c.drawString(100, 660, f"CIF: {self.company_data['cif']}")
            c.drawString(100, 640, f"Direccion: {self.company_data['direccion']}")
            cli = invoice_data.get("cliente", {})
            c.drawString(100, 600, f"Cliente: {cli.get('nombre', '')}")
            c.drawString(100, 580, f"CIF/NIF: {cli.get('cif_nif', '')}")
            y = 540
            for item in invoice_data["productos"]:
                c.drawString(100, y, str(item.get("nombre", ""))[:40])
                c.drawString(350, y, f"{item.get('precio_unitario', 0):.2f} EUR")
                c.drawString(450, y, f"{item.get('iva', 21)}%")
                c.drawString(500, y, f"{item.get('subtotal', 0) + item.get('iva_amount', 0):.2f} EUR")
                y -= 20
            c.drawString(400, y - 20, f"Subtotal: {abs(invoice_data['subtotal']):.2f} EUR")
            c.drawString(400, y - 40, f"IVA: {abs(invoice_data['iva']):.2f} EUR")
            c.drawString(400, y - 60, f"TOTAL: {abs(invoice_data['total']):.2f} EUR")
            if credit_note:
                c.drawString(100, y - 90, f"Motivo: {invoice_data.get('notas', '')[:60]}")
            c.drawString(100, y - 110, "Verificar en GaiaChain: pendiente")
            # Resiliencia legal: si GaiaChain no está disponible, dejamos evidencia textual en el documento.
            # Esto permite que un auditor detecte la continuidad operativa (eIDAS 2, Art. 25.2).
            if not os.path.isfile(self.gaiachain_cli):
                c.setFont("Helvetica-Bold", 8)
                c.drawString(70, max(40, y - 140), "Modo de continuidad operativa (eIDAS 2, Art. 25.2)")
                c.setFont("Helvetica", 8)
                c.drawString(70, max(30, y - 155), "Documento emitido sin acceso a GaiaChain; hash local preserva integridad.")
            c.save()
            return str(path)
        except Exception as e:
            logger.warning("PDF no generado: %s", e)
            return ""

    def _generate_txt_invoice(self, invoice_data: Dict[str, Any], credit_note: bool = False) -> str:
        title = "NOTA DE CREDITO" if credit_note else "FACTURA"
        path = _INVOICES_DIR / f"{'NC' if credit_note else 'FACT'}_{invoice_data['numero_factura'].replace('/', '-')}.txt"
        lines = [
            title,
            f"Numero: {invoice_data['numero_factura']}",
            f"Fecha: {invoice_data['fecha']}",
            f"Emisor: {self.company_data['nombre']}",
            f"Cliente: {invoice_data.get('cliente', {}).get('nombre', '')}",
            f"Subtotal: {abs(invoice_data['subtotal']):.2f} EUR",
            f"IVA: {abs(invoice_data['iva']):.2f} EUR",
            f"TOTAL: {abs(invoice_data['total']):.2f} EUR",
        ]
        if credit_note:
            lines.append(f"Motivo: {invoice_data.get('notas', '')}")
        # Resiliencia legal: si no hay acceso a GaiaChain, añadimos cláusula de continuidad.
        if not os.path.isfile(self.gaiachain_cli):
            lines.extend(
                [
                    "",
                    "--- Modo de continuidad operativa (eIDAS 2, Art. 25.2) ---",
                    "GaiaChain no disponible en el momento de emisión; se preserva integridad con hash local.",
                ]
            )
        path.write_text("\n".join(lines), encoding="utf-8")
        return str(path)

    def _generate_pdf_hash(self, pdf_path: str) -> str:
        try:
            h = hashlib.sha256()
            with open(pdf_path, "rb") as f:
                while chunk := f.read(8192):
                    h.update(chunk)
            return h.hexdigest()
        except Exception:
            return ""

    def _register_in_gaiachain(self, invoice_data: Dict[str, Any], hash_pdf: str) -> str:
        tx_data = {
            "type": "invoice",
            "data": {
                "numero_factura": invoice_data["numero_factura"],
                "cliente": invoice_data.get("cliente", {}).get("cif_nif", ""),
                "productos": invoice_data.get("productos", []),
                "subtotal": invoice_data["subtotal"],
                "iva": invoice_data["iva"],
                "total": invoice_data["total"],
                "fecha": invoice_data["fecha"],
                "normativa": invoice_data.get("normativa", ""),
                "hash_pdf": hash_pdf,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        }
        if not os.path.isfile(self.gaiachain_cli):
            if local_db:
                local_db.log_operation("invoice", tx_data, gaiachain_tx=None, error="gaiachain-cli-missing")
            return "gaiachain-no-cli"
        try:
            r = subprocess.run(
                [self.gaiachain_cli, "record", "--type", "invoice", "--data", json.dumps(tx_data)],
                capture_output=True,
                text=True,
                timeout=15,
            )
            tx = (r.stdout or "").strip()
            if r.returncode == 0:
                return tx or "ok"
            if local_db:
                local_db.log_operation(
                    "invoice",
                    tx_data,
                    gaiachain_tx=None,
                    error=(r.stderr or "gaiachain-error"),
                )
            return f"Error: {r.stderr}"
        except Exception as e:
            logger.warning("GaiaChain invoice: %s", e)
            if local_db:
                local_db.log_operation("invoice", tx_data, gaiachain_tx=None, error=str(e))
            return f"Error: {e}"
