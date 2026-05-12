# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError


class MaterialSale(models.Model):
    _name = "castu.material.sale"
    _description = "Venta de Materiales Compuestos"

    name = fields.Char(string="Número de Venta", required=True, default="/")
    date = fields.Datetime(string="Fecha", default=fields.Datetime.now)
    partner_id = fields.Many2one("res.partner", string="Cliente", required=True)
    sale_line_ids = fields.One2many(
        "castu.material.sale.line",
        "sale_id",
        string="Líneas de Venta",
    )
    state = fields.Selection(
        [
            ("draft", "Borrador"),
            ("confirmed", "Confirmado"),
            ("delivered", "Entregado"),
            ("invoiced", "Facturado"),
        ],
        string="Estado",
        default="draft",
    )
    invoice_id = fields.Many2one("account.move", string="Factura")
    blockchain_tx = fields.Char(string="TX Blockchain")

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", "/") == "/":
                vals["name"] = (
                    self.env["ir.sequence"].next_by_code("castu.material.sale") or "/"
                )
        return super().create(vals_list)

    def action_confirm(self):
        for line in self.sale_line_ids:
            if line.material_id.stock_kg < line.kg:
                raise UserError(
                    f"No hay suficiente stock de {line.material_id.name} (disponible: {line.material_id.stock_kg} kg)"
                )
        self.write({"state": "confirmed"})

    def action_deliver(self):
        self.write({"state": "delivered"})
        self._register_sale_in_blockchain()

    def _register_sale_in_blockchain(self):
        try:
            import urllib.request
            import json
            base = self.env["ir.config_parameter"].get_param(
                "castu.fastapi.url", "http://api:8000"
            )
            payload = {
                "sale_id": self.id,
                "partner_id": self.partner_id.id,
                "lines": [
                    {"material_id": line.material_id.id, "kg": line.kg}
                    for line in self.sale_line_ids
                ],
            }
            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(
                f"{base}/blockchain/material/register_sale",
                data=data,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=10) as r:
                out = json.loads(r.read().decode())
            self.write({"blockchain_tx": out.get("tx_id", "")})
        except Exception:
            pass


class MaterialSaleLine(models.Model):
    _name = "castu.material.sale.line"
    _description = "Línea de Venta de Material"

    sale_id = fields.Many2one("castu.material.sale", string="Venta", ondelete="cascade")
    material_id = fields.Many2one("castu.material", string="Material", required=True)
    kg = fields.Float(string="Cantidad (kg)", required=True)
    price_unit = fields.Float(string="Precio Unitario (€/kg)", required=True)
    subtotal = fields.Float(string="Subtotal (€)", compute="_compute_subtotal", store=True)

    @api.depends("kg", "price_unit")
    def _compute_subtotal(self):
        for line in self:
            line.subtotal = line.kg * line.price_unit
