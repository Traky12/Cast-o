# -*- coding: utf-8 -*-
from odoo import api, fields, models


class EnergiaExcedente(models.Model):
    _name = "castu.energia.excedente"
    _description = "Excedente de Energía (Mercado)"

    name = fields.Char(
        string="ID de Oferta", compute="_compute_name", store=True
    )
    granja_id = fields.Many2one("castu.granja", string="Granja", required=True)
    fecha = fields.Datetime(
        string="Fecha de Generación", default=fields.Datetime.now
    )
    energia_kwh = fields.Float(string="Energía (kWh)", required=True)
    precio_kwh = fields.Float(string="Precio por kWh (€)", required=True)
    tipo = fields.Selection(
        [
            ("solar", "Solar"),
            ("geotermia", "Geotermia"),
            ("hibrida", "Híbrida"),
        ],
        required=True,
        string="Tipo",
    )
    estado = fields.Selection(
        [
            ("disponible", "Disponible"),
            ("vendido", "Vendido"),
            ("cancelado", "Cancelado"),
        ],
        default="disponible",
        string="Estado",
    )
    comprador_id = fields.Many2one("res.partner", string="Comprador")
    biocoin_tx = fields.Char(string="TX BioCoin Castúo")
    contrato_url = fields.Char(string="URL del Contrato (IPFS)")

    @api.depends("granja_id", "fecha")
    def _compute_name(self):
        for record in self:
            f = record.fecha or fields.Datetime.now()
            record.name = f"EXC-{record.granja_id.name or 'G'}-{f.strftime('%Y%m%d%H%M')}"

    def action_vender(self, comprador_id, precio=None):
        """Registra la venta y genera TX/contrato."""
        self.ensure_one()
        if self.estado != "disponible":
            return
        precio = precio or self.precio_kwh
        self.write(
            {
                "estado": "vendido",
                "comprador_id": comprador_id,
                "precio_kwh": precio,
            }
        )
        import hashlib
        data = f"{self.id}-{comprador_id}-{precio}-{self.energia_kwh}"
        self.biocoin_tx = hashlib.sha256(data.encode()).hexdigest()[:32]
        self.contrato_url = f"ipfs://contrato-{self.id}"
