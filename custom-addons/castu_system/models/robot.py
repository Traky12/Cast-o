# -*- coding: utf-8 -*-
"""Robot agrícola autónomo: deshierbe, poda, cosecha. Control vía LoRaWAN/MQTT."""
from odoo import api, fields, models


class AgriculturalRobot(models.Model):
    _name = "castu.robot"
    _description = "Robot Agrícola"

    name = fields.Char(string="Identificador", required=True)
    granja_id = fields.Many2one("castu.granja", string="Granja", required=True)
    tipo = fields.Selection(
        [
            ("deshierbe", "Deshierbe"),
            ("poda", "Poda"),
            ("cosecha", "Cosecha"),
        ],
        required=True,
        string="Tipo",
    )
    estado = fields.Selection(
        [
            ("standby", "En Espera"),
            ("patrulla", "En Patrulla"),
            ("mantenimiento", "Mantenimiento"),
            ("error", "Error"),
        ],
        default="standby",
        string="Estado",
    )
    coordenadas = fields.Char(string="Coordenadas GPS")
    ultimo_contacto = fields.Datetime(string="Último Contacto")
    biocoin_tx = fields.Char(string="TX BioCoin Castúo")
    mqtt_topic = fields.Char(
        string="Topic MQTT",
        compute="_compute_mqtt_topic",
        store=True,
    )

    @api.depends("id")
    def _compute_mqtt_topic(self):
        for r in self:
            r.mqtt_topic = f"castuo/robot/{r.id}/command" if r.id else ""

    def action_start_patrol(self, area=None, speed=0.5):
        """Envía comando al robot para iniciar patrulla (vía backend MQTT)."""
        self.ensure_one()
        if self.estado not in ("standby", "error"):
            return
        self._publish_command(
            "start_patrol",
            {"area": area or "sector_default", "speed": speed},
        )
        self.write({"estado": "patrulla", "ultimo_contacto": fields.Datetime.now()})

    def action_stop(self):
        """Detiene el robot."""
        self.ensure_one()
        self._publish_command("stop", {})
        self.write({"estado": "standby", "ultimo_contacto": fields.Datetime.now()})

    def _publish_command(self, action, params):
        """Publica comando MQTT vía backend FastAPI."""
        try:
            import urllib.request
            import json
            base = self.env["ir.config_parameter"].get_param(
                "castu.fastapi.url", "http://api:8000"
            )
            payload = {
                "robot_id": self.id,
                "command": action,
                "params": params,
            }
            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(
                f"{base}/robotica/command",
                data=data,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            urllib.request.urlopen(req, timeout=5)
        except Exception:
            pass
