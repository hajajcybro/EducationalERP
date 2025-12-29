from odoo import models, fields

class AccountMove(models.Model):
    _inherit = 'account.move'

    fee_invoice_id = fields.Many2one(
        'education.fee.invoice',
        string='Education Fee Invoice',
        ondelete='set null'
    )