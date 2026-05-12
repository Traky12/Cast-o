# -*- coding: utf-8 -*-
from odoo import api, fields, models


class Teledeteccion(models.Model):
    _name = "castu.teledeteccion"
    _description = "Imagen de Teledetección"

    name = fields.Char(string="Nombre", compute="_compute_name", store=True)
    granja_id = fields.Many2one("castu.granja", string="Granja", required=True)
    fecha = fields.Date(string="Fecha", required=True)
    ndvi_promedio = fields.Float(string="NDVI Promedio")
    ndvi_min = fields.Float(string="NDVI Mínimo")
    ndvi_max = fields.Float(string="NDVI Máximo")
    imagen_url = fields.Char(string="URL de la Imagen")
    alert_ids = fields.One2many(
        "castu.teledeteccion.alert", "teledeteccion_id", string="Alertas"
    )
    mision_asociada_id = fields.Many2one(
        "castu.drone.mission", string="Misión Asociada"
    )

    @api.depends("granja_id", "fecha")
    def _compute_name(self):
        for record in self:
            record.name = f"{record.granja_id.name or 'Granja'} - {record.fecha}"

    def action_analizar_ndvi(self):
        """Llama al backend para analizar NDVI (Sentinel/QGIS)."""
        self.ensure_one()
        try:
            import urllib.request
            import json

            base = self.env["ir.config_parameter"].get_param(
                "castu.fastapi.url", "http://api:8000"
            )
            data = json.dumps(
                {
                    "granja_id": self.granja_id.id,
                    "teledeteccion_id": self.id,
                    "imagen_url": self.imagen_url,
                }
            ).encode("utf-8")
            req = urllib.request.Request(
                f"{base}/teledeteccion/analizar",
                data=data,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            urllib.request.urlopen(req, timeout=30)
        except Exception:
            pass


class TeledeteccionAlert(models.Model):
    _name = "castu.teledeteccion.alert"
    _description = "Alerta de Teledetección"

    teledeteccion_id = fields.Many2one(
        "castu.teledeteccion", string="Teledetección", required=True
    )
    tipo = fields.Selection(
        [
            ("estres_hidrico", "Estrés Hídrico"),
            ("plaga", "Plaga Detectada"),
            ("bajo_ndvi", "NDVI Bajo"),
        ],
        required=True,
        string="Tipo",
    )
    zona = fields.Char(string="Zona Afectada")
    ndvi = fields.Float(string="NDVI")
    fecha = fields.Datetime(string="Fecha", default=fields.Datetime.now)
    resuelta = fields.Boolean(string="Resuelta", default=False)

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
                    "channel": "#alertas-teledeteccion",
                    "message": f"🚨 Teledetección: {self.tipo} en {self.zona} (NDVI: {self.ndvi})",
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
