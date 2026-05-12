# -*- coding: utf-8 -*-
from datetime import timedelta
from odoo import api, fields, models


class SistemaRiego(models.Model):
    _name = "castu.riego"
    _description = "Sistema de Riego Automático"

    name = fields.Char(string="Nombre", required=True)
    granja_id = fields.Many2one("castu.granja", string="Granja", required=True)
    tipo = fields.Selection(
        [
            ("goteo", "Goteo"),
            ("aspersion", "Aspersión"),
            ("hidroponia", "Hidroponía"),
            ("aeroponia", "Aeroponía"),
        ],
        required=True,
        string="Tipo",
    )
    valvula_ids = fields.One2many(
        "castu.valvula", "riego_id", string="Válvulas"
    )
    programa = fields.Text(string="Programa Cron")
    ozono = fields.Boolean(string="Con Ozono", default=False)
    ph_objetivo = fields.Float(string="pH Objetivo", default=6.0)
    ec_objetivo = fields.Float(string="EC Objetivo (mS/cm)", default=2.0)
    estado = fields.Selection(
        [
            ("inactivo", "Inactivo"),
            ("activo", "Activo"),
            ("error", "Error"),
        ],
        default="inactivo",
        string="Estado",
    )

    def action_activar_riego(self, duracion_minutos=30, valvula_ids=None):
        """Activa el riego en válvulas específicas o todas."""
        self.ensure_one()
        valvulas = valvula_ids or self.valvula_ids
        for valvula in valvulas:
            valvula.action_abrir()
        ahora = fields.Datetime.now()
        cierre_at = ahora + timedelta(minutes=duracion_minutos)
        self.env["castu.riego.task"].create(
            {
                "riego_id": self.id,
                "accion": "cerrar",
                "tiempo_ejecucion": cierre_at,
                "valvula_ids": [(6, 0, valvulas.ids)],
            }
        )
        self.estado = "activo"
        try:
            import urllib.request
            import json
            base = self.env["ir.config_parameter"].get_param(
                "castu.fastapi.url", "http://api:8000"
            )
            data = json.dumps(
                {"riego_id": self.id, "duracion": duracion_minutos}
            ).encode("utf-8")
            req = urllib.request.Request(
                f"{base}/riego/{self.id}/activar",
                data=data,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            urllib.request.urlopen(req, timeout=5)
        except Exception:
            pass

    def action_ajustar_ph_ec(self, ph=None, ec=None):
        """Ajusta pH y EC (backend dosificadores/ozono)."""
        self.ensure_one()
        try:
            import urllib.request
            import json
            base = self.env["ir.config_parameter"].get_param(
                "castu.fastapi.url", "http://api:8000"
            )
            data = json.dumps({"ph": ph, "ec": ec}).encode("utf-8")
            req = urllib.request.Request(
                f"{base}/riego/{self.id}/ajustar",
                data=data,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            urllib.request.urlopen(req, timeout=5)
        except Exception:
            pass

    def action_decidir_riego(self):
        """Decide si activar riego según sensores y alertas."""
        self.ensure_one()
        sensores = self.env["castu.drone.sensor"].search(
            [("granja_id", "=", self.granja_id.id), ("tipo", "=", "suelo")]
        )
        humedad_promedio = (
            sum(s.valor_actual for s in sensores) / len(sensores)
            if sensores
            else 50
        )
        alertas = self.env["castu.drone.camera.alert"].search(
            [
                ("camera_id.drone_id.granja_id", "=", self.granja_id.id),
                ("tipo", "=", "estres_hidrico"),
                ("resuelta", "=", False),
            ]
        )
        teledeteccion = self.env["castu.teledeteccion"].search(
            [("granja_id", "=", self.granja_id.id)],
            order="fecha desc",
            limit=1,
        )
        ndvi = teledeteccion.ndvi_promedio if teledeteccion else 0.5
        if humedad_promedio < 30 or alertas or ndvi < 0.3:
            self.action_activar_riego(duracion_minutos=45)
            return True
        return False


class Valvula(models.Model):
    _name = "castu.valvula"
    _description = "Válvula de Riego"

    name = fields.Char(string="Nombre", required=True)
    riego_id = fields.Many2one("castu.riego", string="Sistema de Riego")
    estado = fields.Selection(
        [
            ("cerrada", "Cerrada"),
            ("abierta", "Abierta"),
            ("error", "Error"),
        ],
        default="cerrada",
        string="Estado",
    )
    gpio_pin = fields.Integer(string="GPIO Pin")

    def action_abrir(self):
        self.write({"estado": "abierta"})

    def action_cerrar(self):
        self.write({"estado": "cerrada"})


class RiegoTask(models.Model):
    _name = "castu.riego.task"
    _description = "Tarea Programada de Riego"

    riego_id = fields.Many2one("castu.riego", string="Sistema de Riego")
    accion = fields.Selection(
        [
            ("abrir", "Abrir Válvulas"),
            ("cerrar", "Cerrar Válvulas"),
            ("ajustar_ph", "Ajustar pH"),
            ("ajustar_ec", "Ajustar EC"),
        ],
        string="Acción",
    )
    tiempo_ejecucion = fields.Datetime(string="Tiempo de Ejecución")
    valvula_ids = fields.Many2many(
        "castu.valvula",
        "castu_riego_task_valvula_rel",
        "task_id",
        "valvula_id",
        string="Válvulas",
    )
    ejecutado = fields.Boolean(string="Ejecutado", default=False)

    @api.model
    def cron_ejecutar_tareas(self):
        ahora = fields.Datetime.now()
        tareas = self.search(
            [
                ("tiempo_ejecucion", "<=", ahora),
                ("ejecutado", "=", False),
            ]
        )
        for tarea in tareas:
            if tarea.accion == "cerrar":
                for valvula in tarea.valvula_ids:
                    valvula.action_cerrar()
            tarea.write({"ejecutado": True})
        riego_model = self.env["castu.riego"]
        for r in riego_model.search([("estado", "=", "activo")]):
            if not r.valvula_ids.filtered(lambda v: v.estado == "abierta"):
                r.write({"estado": "inactivo"})
