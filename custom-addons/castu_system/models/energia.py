# -*- coding: utf-8 -*-
from odoo import api, fields, models


class EnergiaAgrovoltaica(models.Model):
    _name = "castu.energia"
    _description = "Energía Agrovoltaica"

    name = fields.Char(string="Nombre", required=True)
    granja_id = fields.Many2one("castu.granja", string="Granja", required=True)
    tipo = fields.Selection(
        [
            ("solar", "Paneles Solares"),
            ("geotermia", "Geotermia"),
            ("eolica", "Eólica"),
            ("hibrida", "Híbrida (Solar + Geotermia)"),
        ],
        required=True,
        string="Tipo",
    )
    potencia_actual = fields.Float(string="Potencia Actual (kW)")
    energia_generada = fields.Float(string="Energía Generada Hoy (kWh)")
    bateria_ids = fields.One2many(
        "castu.bateria", "energia_id", string="Baterías"
    )
    estado = fields.Selection(
        [
            ("optima", "Óptima"),
            ("baja", "Baja Generación"),
            ("error", "Error"),
        ],
        default="optima",
        string="Estado",
    )

    def action_optimizar_energia(self):
        """Ajusta generación según demanda (backend Modbus/API)."""
        self.ensure_one()
        try:
            import urllib.request
            import json
            base = self.env["ir.config_parameter"].get_param(
                "castu.fastapi.url", "http://api:8000"
            )
            data = json.dumps({"energia_id": self.id}).encode("utf-8")
            req = urllib.request.Request(
                f"{base}/energia/{self.id}/optimizar",
                data=data,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            urllib.request.urlopen(req, timeout=10)
        except Exception:
            pass


class Bateria(models.Model):
    _name = "castu.bateria"
    _description = "Batería de Almacenamiento"

    name = fields.Char(string="Nombre", required=True)
    energia_id = fields.Many2one(
        "castu.energia", string="Sistema de Energía"
    )
    capacidad = fields.Float(string="Capacidad (kWh)")
    nivel_actual = fields.Float(string="Nivel Actual (%)")
    estado = fields.Selection(
        [
            ("cargando", "Cargando"),
            ("descargando", "Descargando"),
            ("inactiva", "Inactiva"),
        ],
        default="inactiva",
        string="Estado",
    )
