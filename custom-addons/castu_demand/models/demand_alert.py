# -*- coding: utf-8 -*-
from odoo import fields, models


class DemandAlert(models.Model):
    _name = "castu.demand.alert"
    _description = "Alerta de Demanda"

    name = fields.Char("Nombre", required=True)
    description = fields.Text("Descripción")
    type = fields.Selection(
        [("stock", "Stock Insuficiente"), ("production", "Producción Insuficiente")],
        string="Tipo",
    )
    material_id = fields.Many2one("castu.material", "Material")
    date = fields.Datetime("Fecha", default=fields.Datetime.now)
    resolved = fields.Boolean("Resuelta", default=False)
