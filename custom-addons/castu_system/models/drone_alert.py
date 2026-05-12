# -*- coding: utf-8 -*-
from odoo import api, fields, models


class DroneAlert(models.Model):
    _name = "castu.drone.alert"
    _description = "Alerta de Drone"

    drone_id = fields.Many2one("castu.drone", string="Drone", required=True)
    tipo = fields.Selection(
        [
            ("bateria_baja", "Batería Baja"),
            ("fallo_gps", "Fallo de GPS"),
            ("perdida_senal", "Pérdida de Señal"),
            ("mision_fallida", "Misión Fallida"),
        ],
        required=True,
        string="Tipo de Alerta",
    )
    mensaje = fields.Text(string="Mensaje")
    fecha = fields.Datetime(string="Fecha", default=fields.Datetime.now)
    resuelta = fields.Boolean(string="Resuelta", default=False)

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for alert in records:
            alert._notify_slack_telegram()
        return records

    def _notify_slack_telegram(self):
        """Envía notificación a Slack/Telegram (vía FastAPI o parámetros)."""
        try:
            import urllib.request
            import json

            base = self.env["ir.config_parameter"].get_param(
                "castu.fastapi.url", "http://api:8000"
            )
            data = json.dumps(
                {
                    "channel": "#alertas-drones",
                    "message": f"🚨 Alerta drone {self.drone_id.name}: {self.mensaje}",
                }
            ).encode("utf-8")
            req = urllib.request.Request(
                f"{base}/notifications/slack",
                data=data,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            urllib.request.urlopen(req, timeout=3)
        except Exception:
            pass
