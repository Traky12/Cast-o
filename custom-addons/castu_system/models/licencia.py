from odoo import fields, models


class LicenciaAutoconsumo(models.Model):
    _name = "castu.licencia"
    _description = "Licencia de Autoconsumo (RD 244/2019)"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char(string="Número de Licencia", required=True, tracking=True)
    granja_id = fields.Many2one("castu.granja", string="Granja", ondelete="cascade", tracking=True)
    fecha = fields.Date(string="Fecha de Autorización", default=fields.Date.today, tracking=True)
    potencia_kw = fields.Float(string="Potencia Autorizada (kW)", tracking=True)
    rea_numero = fields.Char(string="Número de Registro REA", tracking=True)

    documento_ipfs = fields.Char(string="Hash IPFS del Documento", tracking=True)
    biocoin_tx = fields.Char(string="TX BioCoin Castúo", tracking=True)
    git_commit = fields.Char(string="Git Commit", tracking=True)

    state = fields.Selection(
        [
            ("draft", "Borrador"),
            ("generated", "Documento generado"),
            ("registered", "Registrado"),
        ],
        default="draft",
        tracking=True,
    )

    def action_generar_documento(self):
        # Placeholder: en producción, generar desde templates/legal/licencia_autoconsumo.md y subir a IPFS.
        for rec in self:
            if not rec.biocoin_tx and rec.granja_id and rec.granja_id.biocoin_tx:
                rec.biocoin_tx = rec.granja_id.biocoin_tx
            rec.documento_ipfs = rec.documento_ipfs or "QmXoypizjW3WknFiJnKLwHCnL72vedxjQkDDP1mXWo6uco"
            rec.state = "generated"
        return True

