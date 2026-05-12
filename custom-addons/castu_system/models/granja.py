from odoo import api, fields, models


class Granja(models.Model):
    _name = "castu.granja"
    _description = "Granja Agrovoltaica"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char(string="Nombre", required=True, tracking=True)
    ubicacion = fields.Char(string="Ubicación", tracking=True)
    potencia_kw = fields.Float(string="Potencia Instalada (kW)", tracking=True)

    biocoin_tx = fields.Char(string="TX BioCoin Castúo", tracking=True)
    notes = fields.Text(string="Notas")

    licencia_ids = fields.One2many("castu.licencia", "granja_id", string="Licencias")
    epcis_event_ids = fields.One2many("castu.epcis.event", "granja_id", string="Eventos EPCIS")

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for granja in records:
            if not granja.biocoin_tx:
                granja.biocoin_tx = granja._minar_biocoin(granja.id)
        return records

    def _minar_biocoin(self, granja_id: int) -> str:
        # Stub determinista (32 hex). Sustituir por integración real (Polygon/Ethereum).
        import hashlib

        return hashlib.sha256(str(granja_id).encode()).hexdigest()[:32]

