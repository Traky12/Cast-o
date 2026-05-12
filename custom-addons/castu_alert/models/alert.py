# -*- coding: utf-8 -*-
from odoo import fields, models
import logging

_logger = logging.getLogger(__name__)


class Alert(models.Model):
    _name = "castu.alert"
    _description = "Alerta Predictiva"

    rule_id = fields.Many2one("castu.alert.rule", "Regla", required=True)
    material_id = fields.Many2one("castu.material", "Material")
    current_value = fields.Float("Valor Actual", required=True)
    threshold_value = fields.Float("Valor Umbral", required=True)
    triggered_at = fields.Datetime("Activación", default=fields.Datetime.now)
    resolved_at = fields.Datetime("Resolución")
    severity = fields.Selection(
        [("low", "Baja"), ("medium", "Media"), ("high", "Alta"), ("critical", "Crítica")],
        required=True,
    )
    status = fields.Selection(
        [("triggered", "Activada"), ("acknowledged", "Reconocida"), ("resolved", "Resuelta")],
        default="triggered",
        required=True,
    )
    message = fields.Text("Mensaje", required=True)
    actions_taken = fields.Text("Acciones Tomadas")
    blockchain_tx = fields.Char("TX Blockchain")

    def execute_actions(self):
        for rec in self:
            if rec.rule_id.action == "notify":
                rec._send_notifications()
            # order / adjust: extensible vía otro módulo o cron

    def _send_notifications(self):
        """Envía a Slack/Telegram vía API backend si está configurado."""
        try:
            base = self.env["ir.config_parameter"].get_param("castu.fastapi.url", "http://api:8000")
            import urllib.request
            import json
            payload = json.dumps({
                "alert_id": self.id,
                "name": self.rule_id.name,
                "message": self.message,
                "severity": self.severity,
                "current_value": self.current_value,
                "threshold_value": self.threshold_value,
                "material_name": self.material_id.name if self.material_id else "",
            }).encode("utf-8")
            req = urllib.request.Request(
                f"{base}/notifications/alert",
                data=payload,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=5) as r:
                r.read()
        except Exception as e:
            _logger.warning("Alert notify: %s", e)

    def action_acknowledge(self):
        self.write({"status": "acknowledged"})

    def action_resolve(self):
        self.write({"status": "resolved", "resolved_at": fields.Datetime.now()})
