# -*- coding: utf-8 -*-
from odoo import api, fields, models
import logging

_logger = logging.getLogger(__name__)


class AlertRule(models.Model):
    _name = "castu.alert.rule"
    _description = "Regla de Alerta Predictiva"

    name = fields.Char("Nombre", required=True)
    description = fields.Text("Descripción")
    metric = fields.Selection(
        [
            ("stock", "Stock de Material"),
            ("energy", "Consumo Energético"),
            ("demand", "Demanda Predicha"),
        ],
        required=True,
    )
    material_id = fields.Many2one("castu.material", "Material")
    threshold_type = fields.Selection(
        [("min", "Mínimo"), ("max", "Máximo"), ("change", "Cambio %")],
        required=True,
    )
    threshold_value = fields.Float("Valor Umbral", required=True)
    window_hours = fields.Integer("Ventana (horas)", default=24)
    severity = fields.Selection(
        [("low", "Baja"), ("medium", "Media"), ("high", "Alta"), ("critical", "Crítica")],
        default="medium",
    )
    action = fields.Selection(
        [("notify", "Notificar"), ("order", "Generar Pedido"), ("adjust", "Ajustar Parámetros")],
        default="notify",
    )
    active = fields.Boolean("Activo", default=True)
    last_triggered = fields.Datetime("Última Activación")

    def evaluate(self):
        """Evalúa la regla y crea alerta si se cumple el umbral."""
        for rule in self.filtered("active"):
            value = rule._get_metric_value()
            if value is None:
                continue
            triggered = False
            if rule.threshold_type == "min" and value < rule.threshold_value:
                triggered = True
            elif rule.threshold_type == "max" and value > rule.threshold_value:
                triggered = True
            if triggered:
                msg = rule._message(value)
                self.env["castu.alert"].create({
                    "rule_id": rule.id,
                    "material_id": rule.material_id.id,
                    "current_value": value,
                    "threshold_value": rule.threshold_value,
                    "severity": rule.severity,
                    "message": msg,
                })
                rule.last_triggered = fields.Datetime.now()
                rule.env["castu.alert"].search([("rule_id", "=", rule.id)], order="id desc", limit=1).execute_actions()

    def _get_metric_value(self):
        if self.metric == "stock" and self.material_id:
            return self.material_id.stock_kg
        return None

    def _message(self, value):
        if self.metric == "stock":
            return f"Stock de {self.material_id.name}: {value:.1f} kg (umbral: {self.threshold_value})"
        return f"Alerta: {self.name} (valor: {value}, umbral: {self.threshold_value})"
