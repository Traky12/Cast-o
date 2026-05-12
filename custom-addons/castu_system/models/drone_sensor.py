# -*- coding: utf-8 -*-
from odoo import api, fields, models


class DroneSensor(models.Model):
    _name = "castu.drone.sensor"
    _description = "Sensor IoT para Drones/Granja"

    name = fields.Char(string="Identificador", required=True)
    granja_id = fields.Many2one("castu.granja", string="Granja", required=True)
    tipo = fields.Selection(
        [
            ("temperatura", "Temperatura"),
            ("humedad", "Humedad"),
            ("suelo", "Humedad del Suelo"),
            ("luz", "Luz"),
            ("co2", "CO₂"),
        ],
        required=True,
        string="Tipo",
    )
    valor_actual = fields.Float(string="Valor Actual")
    umbral_min = fields.Float(string="Umbral Mínimo")
    umbral_max = fields.Float(string="Umbral Máximo")
    alert_ids = fields.One2many(
        "castu.drone.sensor.alert", "sensor_id", string="Alertas"
    )

    @api.model
    def update_from_mqtt(self, sensor_id, valor):
        """Actualiza valor desde MQTT/FastAPI."""
        sensor = self.search([("name", "=", sensor_id)], limit=1)
        if not sensor:
            return
        sensor.write({"valor_actual": float(valor)})
        if (sensor.umbral_min and valor < sensor.umbral_min) or (
            sensor.umbral_max and valor > sensor.umbral_max
        ):
            self.env["castu.drone.sensor.alert"].create(
                {
                    "sensor_id": sensor.id,
                    "tipo": "umbral_excedido",
                    "valor": valor,
                    "mensaje": f"Valor {valor} fuera de rango [{sensor.umbral_min}, {sensor.umbral_max}]",
                }
            )


class DroneSensorAlert(models.Model):
    _name = "castu.drone.sensor.alert"
    _description = "Alerta de Sensor IoT"

    sensor_id = fields.Many2one(
        "castu.drone.sensor", string="Sensor", required=True
    )
    tipo = fields.Selection(
        [
            ("umbral_excedido", "Umbral Excedido"),
            ("fallo_sensor", "Fallo del Sensor"),
        ],
        required=True,
        string="Tipo",
    )
    valor = fields.Float(string="Valor")
    mensaje = fields.Text(string="Mensaje")
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
                    "channel": "#alertas-sensores",
                    "message": f"🚨 Alerta sensor {self.sensor_id.name}: {self.mensaje}",
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
