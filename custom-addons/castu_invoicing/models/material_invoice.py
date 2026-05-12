# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError
import base64
import logging

_logger = logging.getLogger(__name__)


class MaterialInvoice(models.Model):
    _name = "castu.material.invoice"
    _description = "Factura de Materiales Compuestos (Facturae SII)"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char("Número de Factura", required=True, default="/", tracking=True)
    date = fields.Date("Fecha", default=fields.Date.today, required=True, tracking=True)
    company_id = fields.Many2one("res.company", "Empresa", default=lambda self: self.env.company)
    partner_id = fields.Many2one("res.partner", "Cliente", required=True, tracking=True)
    sale_id = fields.Many2one("castu.material.sale", "Venta Asociada", ondelete="set null")
    invoice_line_ids = fields.One2many(
        "castu.material.invoice.line",
        "invoice_id",
        "Líneas de Factura",
    )
    amount_total = fields.Float("Total (€)", compute="_compute_amount_total", store=True)
    state = fields.Selection(
        [
            ("draft", "Borrador"),
            ("confirmed", "Confirmada"),
            ("sent", "Enviada a SII"),
            ("paid", "Pagada"),
            ("cancelled", "Cancelada"),
        ],
        string="Estado",
        default="draft",
        tracking=True,
    )
    sii_response = fields.Text("Respuesta SII", readonly=True)
    sii_state = fields.Selection(
        [
            ("not_sent", "No Enviada"),
            ("sent", "Enviada"),
            ("accepted", "Aceptada"),
            ("rejected", "Rechazada"),
        ],
        string="Estado SII",
        default="not_sent",
        tracking=True,
    )
    facturae_xml = fields.Text("XML Facturae", readonly=True)
    blockchain_tx = fields.Char("TX Blockchain", readonly=True, tracking=True)

    @api.depends("invoice_line_ids", "invoice_line_ids.subtotal")
    def _compute_amount_total(self):
        for inv in self:
            inv.amount_total = sum(inv.invoice_line_ids.mapped("subtotal"))

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", "/") == "/":
                vals["name"] = self.env["ir.sequence"].next_by_code("castu.material.invoice") or "/"
        return super().create(vals_list)

    def action_confirm(self):
        self.write({"state": "confirmed"})
        for inv in self:
            inv.facturae_xml = inv._generate_facturae_xml()
        return True

    def action_send_sii(self):
        for inv in self:
            if inv.state != "confirmed":
                raise UserError("Solo se pueden enviar facturas confirmadas.")
            nif = (inv.company_id.vat or "").replace(" ", "")
            clave = self.env["ir.config_parameter"].sudo().get_param("castu_invoicing.sii_clave", "")
            from odoo.addons.castu_invoicing.services.sii_client import send_invoice_to_sii

            response = send_invoice_to_sii(inv.facturae_xml, nif, clave)
            inv.write(
                {
                    "sii_state": "sent",
                    "sii_response": str(response),
                }
            )
            if response.get("Estado") == "Correcto":
                inv.write({"sii_state": "accepted", "state": "sent"})
                inv._register_in_blockchain()
            else:
                inv.write({"sii_state": "rejected"})
        return True

    def _generate_facturae_xml(self):
        from odoo.addons.castu_invoicing.services.facturae_generator import generate_facturae

        return generate_facturae(self)

    def _register_in_blockchain(self):
        try:
            base = self.env["ir.config_parameter"].get_param("castu.fastapi.url", "http://api:8000")
            import urllib.request
            import json

            payload = {
                "invoice_id": self.id,
                "partner_id": self.partner_id.id,
                "amount_total": self.amount_total,
                "date": self.date.isoformat(),
            }
            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(
                f"{base}/blockchain/material/register_invoice",
                data=data,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=10) as r:
                out = json.loads(r.read().decode())
            self.write({"blockchain_tx": out.get("tx_id", "")})
        except Exception as e:
            _logger.warning("Blockchain register invoice: %s", e)

    def action_view_xml(self):
        """Genera y descarga el XML Facturae."""
        self.ensure_one()
        xml = self.facturae_xml or self._generate_facturae_xml()
        if not xml:
            raise UserError("No hay XML Facturae generado.")
        attachment = self.env["ir.attachment"].create(
            {
                "name": f"Facturae_{self.name}.xml",
                "datas": base64.b64encode(xml.encode("utf-8")),
                "res_model": self._name,
                "res_id": self.id,
            }
        )
        return {
            "type": "ir.actions.act_url",
            "url": f"/web/content/{attachment.id}?download=true",
            "target": "self",
        }


class MaterialInvoiceLine(models.Model):
    _name = "castu.material.invoice.line"
    _description = "Línea de Factura de Materiales"

    invoice_id = fields.Many2one("castu.material.invoice", "Factura", ondelete="cascade")
    material_id = fields.Many2one("castu.material", "Material", required=True)
    kg = fields.Float("Cantidad (kg)", required=True)
    price_unit = fields.Float("Precio Unitario (€/kg)", required=True)
    subtotal = fields.Float("Subtotal (€)", compute="_compute_subtotal", store=True)

    @api.depends("kg", "price_unit")
    def _compute_subtotal(self):
        for line in self:
            line.subtotal = line.kg * line.price_unit
