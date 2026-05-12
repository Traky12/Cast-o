# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class CarbonCredit(models.Model):
    _name = "castu.carbon.credit"
    _description = "Crédito de Carbono"

    name = fields.Char("ID del Crédito", compute="_compute_name", store=True)
    material_id = fields.Many2one("castu.material", "Material", required=True)
    production_id = fields.Many2one("castu.material.production", "Producción Asociada")
    kg_produced = fields.Float("kg Producidos", required=True)
    savings_kg_co2 = fields.Float("Ahorro de CO₂ (kg)", required=True)
    date = fields.Date("Fecha", default=fields.Date.today, required=True)
    verification_doc = fields.Binary("Documento de Verificación")
    blockchain_tx = fields.Char("TX Blockchain")
    state = fields.Selection(
        [
            ("draft", "Borrador"),
            ("registered", "Registrado"),
            ("sold", "Vendido"),
            ("cancelled", "Cancelado"),
        ],
        string="Estado",
        default="draft",
    )
    sale_price = fields.Float("Precio de Venta (€)")
    buyer_id = fields.Many2one("res.partner", "Comprador")

    @api.depends("id")
    def _compute_name(self):
        for rec in self:
            rec.name = f"CO2-{rec.id:06d}" if rec.id else "CO2-000000"

    def action_register(self):
        try:
            base = self.env["ir.config_parameter"].get_param("castu.fastapi.url", "http://api:8000")
            import urllib.request
            import json
            for rec in self:
                payload = json.dumps({
                    "material_id": rec.material_id.id,
                    "kg_produced": rec.kg_produced,
                    "savings_kg_co2": rec.savings_kg_co2,
                    "date": rec.date.isoformat(),
                }).encode("utf-8")
                req = urllib.request.Request(
                    f"{base}/blockchain/carbon/register_credit",
                    data=payload,
                    headers={"Content-Type": "application/json"},
                    method="POST",
                )
                with urllib.request.urlopen(req, timeout=10) as r:
                    out = json.loads(r.read().decode())
                rec.write({"state": "registered", "blockchain_tx": out.get("tx_id", "")})
        except Exception as e:
            _logger.warning("Carbon register: %s", e)
            for rec in self:
                rec.write({"state": "registered", "blockchain_tx": "stub-" + str(rec.id)})
        return True

    def action_sell(self):
        self.ensure_one()
        if self.state != "registered":
            raise UserError("Solo se pueden vender créditos registrados.")
        return {
            "type": "ir.actions.act_window",
            "res_model": "castu.carbon.credit.sell.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {"default_credit_id": self.id},
        }


class CarbonCreditSellWizard(models.TransientModel):
    _name = "castu.carbon.credit.sell.wizard"
    _description = "Venta de Crédito de Carbono"

    credit_id = fields.Many2one("castu.carbon.credit", "Crédito", required=True)
    buyer_id = fields.Many2one("res.partner", "Comprador", required=True)
    price_per_ton = fields.Float("Precio (€/ton CO₂)", default=80.0)

    def action_confirm(self):
        self.ensure_one()
        credit = self.credit_id
        try:
            base = self.env["ir.config_parameter"].get_param("castu.fastapi.url", "http://api:8000")
            import urllib.request
            import json
            payload = json.dumps({
                "credit_id": credit.id,
                "buyer_id": self.buyer_id.id,
                "price_per_ton": self.price_per_ton,
            }).encode("utf-8")
            req = urllib.request.Request(
                f"{base}/blockchain/carbon/sell_credit",
                data=payload,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=10) as r:
                out = json.loads(r.read().decode())
            tx = out.get("tx_id", "")
        except Exception:
            tx = "stub-sell-" + str(credit.id)
        credit.write({
            "state": "sold",
            "buyer_id": self.buyer_id.id,
            "sale_price": (credit.savings_kg_co2 / 1000.0) * self.price_per_ton,
            "blockchain_tx": tx,
        })
        return {"type": "ir.actions.act_window_close"}
