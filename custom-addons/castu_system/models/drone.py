# -*- coding: utf-8 -*-
from odoo import api, fields, models


class Drone(models.Model):
    _name = "castu.drone"
    _description = "Drone Castuo Link"

    name = fields.Char(string="Identificador", required=True)
    granja_id = fields.Many2one("castu.granja", string="Granja", required=True)
    modelo = fields.Selection(
        [
            ("mavic", "DJI Mavic"),
            ("phantom", "DJI Phantom"),
            ("custom", "Personalizado (ArduPilot)"),
        ],
        default="custom",
        string="Modelo",
    )
    estado = fields.Selection(
        [
            ("standby", "En Espera"),
            ("mission", "En Misión"),
            ("returning", "Regresando"),
            ("error", "Error"),
        ],
        default="standby",
        string="Estado",
    )
    bateria = fields.Float(string="Batería (%)", default=100.0)
    latitud = fields.Float(string="Latitud", digits=(9, 6))
    longitud = fields.Float(string="Longitud", digits=(9, 6))
    altitud = fields.Float(string="Altitud (m)", digits=(6, 2))
    mision_actual_id = fields.Many2one(
        "castu.drone.mission", string="Misión Actual", readonly=True
    )
    biocoin_tx = fields.Char(string="TX BioCoin Castúo")
    ultimo_contacto = fields.Datetime(string="Último Contacto")
    mission_ids = fields.One2many(
        "castu.drone.mission", "drone_id", string="Misiones"
    )
    alert_ids = fields.One2many(
        "castu.drone.alert", "drone_id", string="Alertas"
    )

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for drone in records:
            if not drone.biocoin_tx:
                drone.biocoin_tx = drone._minar_biocoin(drone.id)
        return records

    def _minar_biocoin(self, drone_id):
        import hashlib
        return hashlib.sha256(str(drone_id).encode()).hexdigest()[:32]

    def update_telemetry(self, lat, lon, alt, battery):
        self.ensure_one()
        estado = "mission" if battery > 20 else "error"
        self.write(
            {
                "latitud": lat,
                "longitud": lon,
                "altitud": alt,
                "bateria": battery,
                "estado": estado,
                "ultimo_contacto": fields.Datetime.now(),
            }
        )
        if battery < 20:
            self.env["castu.drone.alert"].create(
                {
                    "drone_id": self.id,
                    "tipo": "bateria_baja",
                    "mensaje": f"Batería baja: {battery}%",
                }
            )

    def action_start_mission_mapping(self):
        self.ensure_one()
        return self._start_mission("mapping", {})

    def action_start_mission_spraying(self):
        self.ensure_one()
        return self._start_mission("spraying", {})

    def _start_mission(self, mission_type, params):
        self.ensure_one()
        if self.estado != "standby":
            return
        mission = self.env["castu.drone.mission"].create(
            {
                "drone_id": self.id,
                "tipo": mission_type,
                "params": str(params),
                "estado": "pending",
            }
        )
        mission.action_start()
        self.write({"mision_actual_id": mission.id, "estado": "mission"})
        # Llamada a FastAPI (backend) para iniciar misión real
        self._call_fastapi_start_mission(mission.id, mission_type, params)
        return mission

    def _call_fastapi_start_mission(self, mission_id, mission_type, params):
        """Llama al backend FastAPI para iniciar la misión en el drone (MAVLink)."""
        try:
            import urllib.request
            import json

            base = self.env["ir.config_parameter"].get_param(
                "castu.fastapi.url", "http://api:8000"
            )
            data = json.dumps(
                {
                    "mission_id": str(mission_id),
                    "drone_id": str(self.id),
                    "mission_type": mission_type,
                    "waypoints": params.get("waypoints", []),
                }
            ).encode("utf-8")
            req = urllib.request.Request(
                f"{base}/drones/{self.id}/start_mission",
                data=data,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            urllib.request.urlopen(req, timeout=5)
        except Exception:
            pass  # En desarrollo puede no estar el backend
