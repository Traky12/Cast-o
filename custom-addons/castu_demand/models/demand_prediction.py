# -*- coding: utf-8 -*-
from odoo import api, fields, models
import json
import logging

_logger = logging.getLogger(__name__)


class DemandPrediction(models.Model):
    _name = "castu.demand.prediction"
    _description = "Predicción de Demanda de Materiales"

    material_id = fields.Many2one("castu.material", "Material", required=True)
    date = fields.Date("Fecha de Predicción", default=fields.Date.today, required=True)
    predictions = fields.Text("Predicciones (JSON)")  # JSON list of {date, kg}
    method = fields.Selection(
        [("ai", "IA (Mistral)"), ("fallback", "Respaldo (Promedio Móvil)")],
        string="Método",
        default="fallback",
    )
    accuracy = fields.Float("Precisión (0-1)", digits=(3, 2))
    alert_generated = fields.Boolean("Alerta Generada", default=False)

    def _get_fastapi_url(self):
        return self.env["ir.config_parameter"].get_param("castu.fastapi.url", "http://api:8000")

    def _get_history_kg_sold(self, material_id, limit=90):
        """Últimos kg vendidos por fecha (desde castu.material.sale.line)."""
        lines = self.env["castu.material.sale.line"].search(
            [("material_id", "=", material_id), ("sale_id.state", "in", ["delivered", "invoiced"])],
            order="sale_id.date desc",
            limit=limit,
        )
        by_date = {}
        for line in lines:
            dt = line.sale_id.date.date() if line.sale_id.date else fields.Date.today()
            by_date[dt] = by_date.get(dt, 0) + line.kg
        return [{"date": str(k), "kg": v} for k, v in sorted(by_date.items(), reverse=True)[:30]]

    @api.model
    def generate_predictions(self, material_ids=None, days_ahead=7):
        """Genera predicciones para materiales (vía API /ia/predict_demand)."""
        materials = self.env["castu.material"].search([])
        if material_ids:
            materials = materials.filtered(lambda m: m.id in material_ids)
        for material in materials:
            try:
                import urllib.request

                history = self._get_history_kg_sold(material.id)
                payload = json.dumps({
                    "material_id": material.id,
                    "days_ahead": days_ahead,
                    "use_ai": False,
                    "history_kg_sold": history,
                }).encode("utf-8")
                base = self._get_fastapi_url()
                req = urllib.request.Request(
                    f"{base}/ia/predict_demand",
                    data=payload,
                    headers={"Content-Type": "application/json"},
                    method="POST",
                )
                with urllib.request.urlopen(req, timeout=15) as r:
                    out = json.loads(r.read().decode())
                self.create({
                    "material_id": material.id,
                    "predictions": json.dumps(out.get("predictions", [])),
                    "method": "ai" if out.get("method") != "fallback" else "fallback",
                })
                self._check_stock_alerts(material, out.get("predictions", []))
            except Exception as e:
                _logger.warning("Demand prediction for material %s: %s", material.name, e)

    def _check_stock_alerts(self, material, predictions):
        total_demand = sum(p.get("kg", 0) for p in predictions)
        margin = 1.2
        if material.stock_kg < total_demand * margin:
            self.env["castu.demand.alert"].create({
                "name": f"Stock bajo para {material.name}",
                "description": f"Demanda prevista: {total_demand:.1f} kg, Stock actual: {material.stock_kg:.1f} kg",
                "type": "stock",
                "material_id": material.id,
            })
            for rec in self.search([("material_id", "=", material.id)], limit=1):
                rec.alert_generated = True
