# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class AccountMoveReversal(models.TransientModel):
    _inherit = 'account.move.reversal'

    currency_id = fields.Many2one(
        'res.currency',
        readonly=True
    )

    is_due_amount_different = fields.Boolean(
        string="Due Amount Differs",
    )

    reverse_amount = fields.Monetary(
        string='Reverse Amount',
        currency_field='currency_id',
        required=True
    )

    def action_reverse_and_create_invoice(self):
        res = super().action_reverse_and_create_invoice()

        new_move = self.env['account.move'].browse(res.get('res_id'))
        if not new_move:
            return res

        if self.is_due_amount_different and self.reverse_amount:
            # Remove existing invoice lines
            new_move.invoice_line_ids.unlink()

            # Add ONLY reverse amount line
            new_move.write({
                'invoice_line_ids': [
                    (0, 0, {
                        'name': _('Adjusted Reverse Amount'),
                        'quantity': 1,
                        'price_unit': self.reverse_amount,
                    })
                ]
            })

        return res

