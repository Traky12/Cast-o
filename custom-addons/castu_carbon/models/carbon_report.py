# -*- coding: utf-8 -*-
from odoo import api, fields, models
from datetime import timedelta


class CarbonReport(models.Model):
    _name = "castu.carbon.report"
    _description = "Reporte de Créditos de Carbono"

    date_from = fields.Date(
        "Desde",
        required=True,
        default=lambda self: fields.Date.today() - timedelta(days=30),
    )
    date_to = fields.Date("Hasta", required=True, default=fields.Date.today)
    total_credits = fields.Float("Créditos Totales (kg CO₂)", compute="_compute_totals", store=True)
    total_revenue = fields.Float("Ingresos por Ventas (€)", compute="_compute_totals", store=True)
    state = fields.Selection([("draft", "Borrador"), ("generated", "Generado")], default="draft")

    @api.depends("date_from", "date_to")
    def _compute_totals(self):
        for report in self:
            credits = self.env["castu.carbon.credit"].search([
                ("date", ">=", report.date_from),
                ("date", "<=", report.date_to),
            ])
            report.total_credits = sum(c.savings_kg_co2 for c in credits)
            report.total_revenue = sum(c.sale_price for c in credits if c.state == "sold")

    def action_generate(self):
        self.write({"state": "generated"})
        return True
