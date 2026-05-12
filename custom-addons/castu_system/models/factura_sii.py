from odoo import fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    biocoin_tx = fields.Char(string="TX BioCoin Castúo", tracking=True)
    git_commit = fields.Char(string="Git Commit", tracking=True)

    def action_post(self):
        res = super().action_post()
        for inv in self:
            if not inv.biocoin_tx:
                inv.biocoin_tx = inv._minar_biocoin(inv.id)
        return res

    def _minar_biocoin(self, invoice_id: int) -> str:
        # Stub determinista (32 hex). Sustituir por integración real (Polygon/Ethereum).
        import hashlib

        return hashlib.sha256(str(invoice_id).encode()).hexdigest()[:32]

    def action_enviar_sii(self):
        # Placeholder: generar Facturae (3.2.1) y enviar a SII/FACe.
        return True

