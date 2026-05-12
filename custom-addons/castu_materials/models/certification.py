# -*- coding: utf-8 -*-
from odoo import api, fields, models


class MaterialCertification(models.Model):
    _name = "castu.material.certification"
    _description = "Certificación Ecológica"

    name = fields.Char(string="Número de Certificación", required=True, default="/")
    production_id = fields.Many2one(
        "castu.material.production",
        string="Lote de Producción",
    )
    material_id = fields.Many2one(
        "castu.material",
        string="Material",
        related="production_id.material_id",
        store=True,
    )
    certification_body = fields.Selection(
        [
            ("une", "UNE (España)"),
            ("din_certco", "DIN CERTCO (Alemania)"),
            ("usda", "USDA (EE.UU.)"),
            ("ecocert", "EcoCert (UE)"),
        ],
        string="Organismo Certificador",
        required=True,
    )
    date = fields.Date(string="Fecha de Certificación", default=fields.Date.today)
    validity = fields.Date(string="Validez")
    document = fields.Binary(string="Documento de Certificación")
    blockchain_tx = fields.Char(string="TX Blockchain")

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", "/") == "/":
                vals["name"] = (
                    self.env["ir.sequence"].next_by_code("castu.material.certification")
                    or "/"
                )
        return super().create(vals_list)

    def action_register_blockchain(self):
        try:
            import urllib.request
            import json
            base = self.env["ir.config_parameter"].get_param(
                "castu.fastapi.url", "http://api:8000"
            )
            payload = {
                "certification_id": self.id,
                "certification_body": self.certification_body,
                "date": self.date.isoformat() if self.date else "",
                "validity": self.validity.isoformat() if self.validity else "",
            }
            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(
                f"{base}/blockchain/material/register_certification",
                data=data,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=10) as r:
                out = json.loads(r.read().decode())
            self.write({"blockchain_tx": out.get("tx_id", "")})
        except Exception:
            pass
