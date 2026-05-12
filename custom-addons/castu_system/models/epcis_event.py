from odoo import fields, models


class EPCISEvent(models.Model):
    _name = "castu.epcis.event"
    _description = "Evento EPCIS"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char(string="Evento ID", tracking=True)
    event_time = fields.Datetime(string="Fecha/Hora", default=fields.Datetime.now, tracking=True)
    event_type = fields.Selection(
        [("ObjectEvent", "Object Event"), ("AggregationEvent", "Aggregation Event")],
        default="ObjectEvent",
        tracking=True,
    )
    biz_step = fields.Char(string="Paso de Negocio", tracking=True)
    epc = fields.Char(string="EPC (GTIN/SSCC)", tracking=True)
    tx_hash = fields.Char(string="TX BioCoin Castúo", tracking=True)
    git_commit = fields.Char(string="Git Commit", tracking=True)
    granja_id = fields.Many2one("castu.granja", string="Granja", ondelete="cascade", tracking=True)

    state = fields.Selection(
        [("draft", "Borrador"), ("sent", "Enviado")],
        default="draft",
        tracking=True,
    )

    def action_send_to_epcis(self):
        # Placeholder: integrar con OpenEPCIS (service openepcis:8080) o proxy EPCIS.
        for rec in self:
            rec.state = "sent"
        return True

