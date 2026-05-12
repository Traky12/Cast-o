# -*- coding: utf-8 -*-
"""Materiales compuestos ecológicos (residuos agrícolas → drones, paneles, sensores)."""
from odoo import api, fields, models

CONVERSION_RATE = {
    "hemp_composite": 0.8,
    "pla_starch": 0.9,
    "cellulose_nano": 0.75,
    "magnesium_alloy": 0.95,
}


class MaterialCompuesto(models.Model):
    _name = "castu.material.compuesto"
    _description = "Material Compuesto Ecológico"

    name = fields.Char(string="Nombre", required=True)
    tipo = fields.Selection(
        [
            ("hemp_composite", "Bio-compuesto de Cáñamo"),
            ("pla_starch", "PLA con Almidón"),
            ("cellulose_nano", "Nanocompuesto de Celulosa"),
            ("magnesium_alloy", "Aleación de Magnesio"),
        ],
        required=True,
        string="Tipo",
    )
    materia_prima = fields.Selection(
        [
            ("hemp", "Cáñamo"),
            ("potato", "Patata"),
            ("wheat", "Trigo"),
            ("corn", "Maíz"),
        ],
        required=True,
        string="Materia Prima",
    )
    propiedades = fields.Text(string="Propiedades")
    stock_kg = fields.Float(string="Stock (kg)", default=0.0)
    precio_kg = fields.Float(string="Precio por kg (€)")
    aplicacion_default = fields.Selection(
        [
            ("drones", "Piezas de Drones"),
            ("invernaderos", "Paneles para Invernaderos"),
            ("sensores", "Sensores Biodegradables"),
            ("riego", "Sistemas de Riego"),
        ],
        string="Aplicación Principal",
    )
    biocoin_tx = fields.Char(string="TX BioCoin (trazabilidad)")

    def action_producir(self, kg_materia_prima=10.0):
        """Simula producción: materia prima → material compuesto (tasa de conversión)."""
        self.ensure_one()
        rate = CONVERSION_RATE.get(self.tipo, 0.8)
        kg_producido = kg_materia_prima * rate
        self.stock_kg += kg_producido
        return kg_producido


class AplicacionMaterial(models.Model):
    _name = "castu.material.aplicacion"
    _description = "Aplicación de Materiales Compuestos"

    name = fields.Char(string="Referencia", compute="_compute_name", store=True)
    material_id = fields.Many2one(
        "castu.material.compuesto",
        string="Material",
        required=True,
    )
    producto_final = fields.Selection(
        [
            ("drone_wing", "Ala de Drone"),
            ("drone_frame", "Carcasa de Drone"),
            ("solar_panel", "Panel Solar Agrovoltaico"),
            ("soil_sensor", "Sensor de Suelo Biodegradable"),
            ("irrigation_pipe", "Tubería de Riego"),
        ],
        required=True,
        string="Producto Final",
    )
    cantidad = fields.Integer(string="Cantidad producida", default=1)
    kg_consumidos = fields.Float(string="Kg material consumidos")
    fecha = fields.Datetime(
        string="Fecha de Producción",
        default=fields.Datetime.now,
    )
    granja_destino_id = fields.Many2one(
        "castu.granja",
        string="Granja Destino",
    )

    @api.depends("material_id", "producto_final", "fecha")
    def _compute_name(self):
        for rec in self:
            f = rec.fecha or fields.Datetime.now()
            rec.name = f"APP-{rec.material_id.name or 'MAT'}-{rec.producto_final or ''}-{f.strftime('%Y%m%d')}"
