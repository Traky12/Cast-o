# -*- coding: utf-8 -*-
from odoo import api, fields, models


class DroneCamera(models.Model):
    _name = "castu.drone.camera"
    _description = "Cámara de Drone"

    name = fields.Char(string="Identificador", required=True)
    drone_id = fields.Many2one("castu.drone", string="Drone", required=True)
    rtsp_url = fields.Char(string="URL RTSP", required=True)
    estado = fields.Selection(
        [("active", "Activa"), ("inactive", "Inactiva")],
        default="active",
        string="Estado",
    )
    resolucion = fields.Char(string="Resolución (ej: 1920x1080)")
    fps = fields.Integer(string="FPS")
    alert_ids = fields.One2many(
        "castu.drone.camera.alert", "camera_id", string="Alertas"
    )

    def action_start_stream(self):
        """Inicia el procesamiento de la cámara (backend FastAPI)."""
        self.ensure_one()
        try:
            import urllib.request
            import json

            base = self.env["ir.config_parameter"].get_param(
                "castu.fastapi.url", "http://api:8000"
            )
            data = json.dumps(
                {"rtsp_url": self.rtsp_url, "drone_id": self.drone_id.id}
            ).encode("utf-8")
            req = urllib.request.Request(
                f"{base}/cameras/stream/start",
                data=data,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            urllib.request.urlopen(req, timeout=5)
        except Exception:
            pass


class DroneCameraAlert(models.Model):
    _name = "castu.drone.camera.alert"
    _description = "Alerta de Cámara"

    camera_id = fields.Many2one(
        "castu.drone.camera", string="Cámara", required=True
    )
    tipo = fields.Selection(
        [
            ("plaga", "Plaga Detectada"),
            ("enfermedad", "Enfermedad Detectada"),
            ("estres_hidrico", "Estrés Hídrico"),
            ("otro", "Otro"),
        ],
        required=True,
        string="Tipo",
    )
    confianza = fields.Float(string="Confianza (%)")
    imagen_url = fields.Char(string="URL de la Imagen")
    fecha = fields.Datetime(string="Fecha", default=fields.Datetime.now)
    coordenadas = fields.Char(string="Coordenadas (lat,lon)")
    resuelta = fields.Boolean(string="Resuelta", default=False)
    biocoin_tx = fields.Char(string="TX BioCoin Castúo")

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for alert in records:
            alert._notify_slack()
        return records

    def _notify_slack(self):
        try:
            import urllib.request
            import json

            base = self.env["ir.config_parameter"].get_param(
                "castu.fastapi.url", "http://api:8000"
            )
            data = json.dumps(
                {
                    "channel": "#alertas-drones",
                    "message": f"🚨 Alerta cámara {self.camera_id.name}: {self.tipo} (Confianza: {self.confianza}%)",
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
