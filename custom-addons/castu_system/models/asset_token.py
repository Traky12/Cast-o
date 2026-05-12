# -*- coding: utf-8 -*-
"""Tokenización de activos en red privada (1 token = activo real, ej. m² cultivo)."""
from odoo import api, fields, models


class AssetToken(models.Model):
    _name = "castu.asset.token"
    _description = "Token de Activo Agrícola"

    name = fields.Char(string="Nombre del Token", required=True)
    asset_id = fields.Many2one(
        "castu.granja",
        string="Activo Respaldado",
        required=True,
    )
    total_supply = fields.Integer(string="Oferta Total", required=True)
    circulating_supply = fields.Integer(
        string="En Circulación",
        default=0,
        readonly=True,
    )
    owner_id = fields.Many2one(
        "res.partner",
        string="Emisor / Dueño Actual",
    )
    blockchain_tx = fields.Char(string="TX en Blockchain Privada")
    unidad_respaldo = fields.Char(
        string="Unidad de Respaldo",
        default="m²",
        help="Ej: 1 token = 1 m² de cultivo",
    )
    state = fields.Selection(
        [
            ("draft", "Borrador"),
            ("active", "Activo"),
            ("closed", "Cerrado"),
        ],
        default="draft",
        string="Estado",
    )

    def action_create_on_chain(self):
        """Registra el token en la blockchain privada (backend/Hyperledger stub)."""
        self.ensure_one()
        if self.state != "draft":
            return
        try:
            import urllib.request
            import json
            base = self.env["ir.config_parameter"].get_param(
                "castu.fastapi.url", "http://api:8000"
            )
            payload = {
                "asset_id": self.asset_id.id,
                "token_name": self.name,
                "total_supply": self.total_supply,
            }
            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(
                f"{base}/blockchain/token/create",
                data=data,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                out = json.loads(resp.read().decode())
            self.write(
                {
                    "blockchain_tx": out.get("tx_id", ""),
                    "state": "active",
                    "circulating_supply": 0,
                }
            )
        except Exception:
            pass

    def action_transfer(self, new_owner_id, amount):
        """Transfiere tokens a otro propietario (vía blockchain privada)."""
        self.ensure_one()
        if self.circulating_supply + amount > self.total_supply:
            return
        try:
            import urllib.request
            import json
            base = self.env["ir.config_parameter"].get_param(
                "castu.fastapi.url", "http://api:8000"
            )
            payload = {
                "token_name": self.name,
                "new_owner_id": new_owner_id,
                "amount": amount,
            }
            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(
                f"{base}/blockchain/token/transfer",
                data=data,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            urllib.request.urlopen(req, timeout=10)
            self.write({"circulating_supply": self.circulating_supply + amount})
        except Exception:
            pass
