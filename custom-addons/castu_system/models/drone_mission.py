# -*- coding: utf-8 -*-
from odoo import api, fields, models


class DroneMission(models.Model):
    _name = "castu.drone.mission"
    _description = "Misión de Drone"

    name = fields.Char(string="Nombre", compute="_compute_name", store=True)
    drone_id = fields.Many2one("castu.drone", string="Drone", required=True)
    tipo = fields.Selection(
        [
            ("mapping", "Mapeo"),
            ("spraying", "Fumigación"),
            ("monitoring", "Monitoreo"),
            ("custom", "Personalizada"),
        ],
        required=True,
        string="Tipo de Misión",
    )
    params = fields.Text(string="Parámetros")
    estado = fields.Selection(
        [
            ("pending", "Pendiente"),
            ("in_progress", "En Progreso"),
            ("completed", "Completada"),
            ("failed", "Fallida"),
        ],
        default="pending",
        string="Estado",
    )
    fecha_inicio = fields.Datetime(string="Fecha de Inicio")
    fecha_fin = fields.Datetime(string="Fecha de Fin")
    biocoin_tx = fields.Char(string="TX BioCoin Castúo")
    resultados = fields.Text(string="Resultados")

    @api.depends("drone_id", "tipo", "fecha_inicio")
    def _compute_name(self):
        for mission in self:
            d = mission.fecha_inicio or fields.Datetime.now()
            mission.name = f"{mission.drone_id.name or 'Drone'} - {mission.tipo} - {d}"

    def action_start(self):
        self.write(
            {
                "estado": "in_progress",
                "fecha_inicio": fields.Datetime.now(),
            }
        )
        if not self.biocoin_tx:
            self.biocoin_tx = self._minar_biocoin(self.id)

    def action_complete(self, resultados=""):
        self.write(
            {
                "estado": "completed",
                "fecha_fin": fields.Datetime.now(),
                "resultados": resultados,
            }
        )
        self.drone_id.write({"mision_actual_id": False, "estado": "standby"})

    def action_fail(self, error=""):
        self.write(
            {
                "estado": "failed",
                "fecha_fin": fields.Datetime.now(),
                "resultados": f"Error: {error}",
            }
        )
        self.drone_id.write({"mision_actual_id": False, "estado": "error"})

    def _minar_biocoin(self, mission_id):
        import hashlib
        return hashlib.sha256(str(mission_id).encode()).hexdigest()[:32]
