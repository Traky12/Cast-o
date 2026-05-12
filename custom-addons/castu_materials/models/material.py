# -*- coding: utf-8 -*-
from odoo import api, fields, models


class Material(models.Model):
    _name = "castu.material"
    _description = "Material Compuesto Ecológico (inventario y ventas)"

    name = fields.Char(string="Nombre", required=True)
    code = fields.Char(string="Código", required=True)
    type = fields.Selection(
        [
            ("hemp_composite", "Bio-compuesto de Cáñamo"),
            ("pla_starch", "PLA con Almidón"),
            ("cellulose_nano", "Nanocompuesto de Celulosa"),
            ("magnesium_alloy", "Aleación de Magnesio"),
        ],
        string="Tipo",
        required=True,
    )
    raw_materials = fields.Selection(
        [
            ("hemp", "Cáñamo"),
            ("potato", "Patata"),
            ("wheat", "Trigo"),
            ("corn", "Maíz"),
        ],
        string="Materia Prima",
        required=True,
    )
    properties = fields.Text(string="Propiedades")
    density = fields.Float(string="Densidad (kg/m³)")
    tensile_strength = fields.Float(string="Resistencia a la tracción (MPa)")
    biodegradable = fields.Boolean(string="Biodegradable", default=True)
    price_per_kg = fields.Float(string="Precio por kg (€)", digits=(6, 2))
    stock_kg = fields.Float(string="Stock (kg)", compute="_compute_stock", store=True)
    image = fields.Binary(string="Imagen")

    production_ids = fields.One2many(
        "castu.material.production",
        "material_id",
        string="Producciones",
    )
    sale_line_ids = fields.One2many(
        "castu.material.sale.line",
        "material_id",
        string="Líneas de Venta",
    )

    @api.depends("production_ids.state", "production_ids.kg_produced", "sale_line_ids.sale_id.state", "sale_line_ids.kg")
    def _compute_stock(self):
        for material in self:
            total_produced = sum(
                p.kg_produced for p in material.production_ids if p.state == "done"
            )
            total_sold = sum(
                line.kg
                for line in material.sale_line_ids
                if line.sale_id.state in ("delivered", "invoiced")
            )
            material.stock_kg = total_produced - total_sold
