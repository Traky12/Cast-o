# -*- coding: utf-8 -*-
from odoo import api, fields, models


class MaterialProduction(models.Model):
    _name = "castu.material.production"
    _description = "Producción de Materiales Compuestos (lotes)"

    name = fields.Char(string="Número de Lote", required=True, default="/")
    material_id = fields.Many2one("castu.material", string="Material", required=True)
    date = fields.Datetime(string="Fecha de Producción", default=fields.Datetime.now)
    kg_produced = fields.Float(string="kg Producidos", required=True)
    raw_material_kg = fields.Float(string="kg Materia Prima Usada")
    energy_kwh = fields.Float(string="Energía Consumida (kWh)")
    operator_id = fields.Many2one(
        "res.users",
        string="Operador",
        default=lambda self: self.env.user,
    )
    state = fields.Selection(
        [
            ("draft", "Borrador"),
            ("producing", "En Producción"),
            ("done", "Finalizado"),
            ("cancelled", "Cancelado"),
        ],
        string="Estado",
        default="draft",
    )
    blockchain_tx = fields.Char(string="TX Blockchain")
    certification_ids = fields.One2many(
        "castu.material.certification",
        "production_id",
        string="Certificaciones",
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", "/") == "/":
                vals["name"] = (
                    self.env["ir.sequence"].next_by_code("castu.material.production")
                    or "/"
                )
        return super().create(vals_list)

    def action_produce(self):
        """Inicia la producción y envía comando a la extrusora vía API/MQTT."""
        self.write({"state": "producing"})
        try:
            import urllib.request
            import json
            base = self.env["ir.config_parameter"].get_param(
                "castu.fastapi.url", "http://api:8000"
            )
            payload = {
                "command": "START_EXTRUSION",
                "material_type": self.material_id.type,
                "kg": self.kg_produced,
            }
            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(
                f"{base}/extrusora/command",
                data=data,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            urllib.request.urlopen(req, timeout=5)
        except Exception:
            pass

    def action_stop_extrusion(self):
        """Detiene la extrusora (comando STOP_EXTRUSION)."""
        try:
            import urllib.request
            import json
            base = self.env["ir.config_parameter"].get_param(
                "castu.fastapi.url", "http://api:8000"
            )
            payload = {"command": "STOP_EXTRUSION"}
            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(
                f"{base}/extrusora/command",
                data=data,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            urllib.request.urlopen(req, timeout=5)
        except Exception:
            pass

    def action_done(self):
        """Finaliza la producción y registra en blockchain."""
        self.write({"state": "done"})
        self._register_in_blockchain()

    def _register_in_blockchain(self):
        try:
            import urllib.request
            import json
            base = self.env["ir.config_parameter"].get_param(
                "castu.fastapi.url", "http://api:8000"
            )
            payload = {
                "material_id": self.material_id.id,
                "kg_produced": self.kg_produced,
                "raw_material_kg": self.raw_material_kg,
                "energy_kwh": self.energy_kwh,
            }
            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(
                f"{base}/blockchain/material/register_production",
                data=data,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=10) as r:
                out = json.loads(r.read().decode())
            self.write({"blockchain_tx": out.get("tx_id", "")})
        except Exception:
            pass
