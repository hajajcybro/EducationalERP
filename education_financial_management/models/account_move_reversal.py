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
        string="Partial Refund",
    )
    reverse_amount = fields.Monetary(
        string='Reverse Amount',
        currency_field='currency_id',
        required=True
    )

    def action_reverse_and_create_invoice(self):
        """Reverse the original move and create a new invoice.
        If a custom reverse amount is provided, replace existing
        invoice lines with a single adjusted amount line."""
        res = super().action_reverse_and_create_invoice()
        new_move = self.env['account.move'].browse(res.get('res_id'))
        if not new_move:
            return res
        if self.is_due_amount_different and self.reverse_amount:
            # Remove existing invoice lines
            new_move.invoice_line_ids.unlink()
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

    def refund_moves(self):
        """Create refund journal entries.
        - Link credit note to refund request
        - Support partial refund when Due Amount Differs is enabled
        """
        self.ensure_one()
        res = super().refund_moves()
        credit_note_id = res.get('res_id')
        credit_note = self.env['account.move'].browse(credit_note_id)
        if self.is_due_amount_different and self.reverse_amount and credit_note:
            credit_note.invoice_line_ids.unlink()
            self.env['account.move.line'].create({
                'move_id': credit_note.id,
                'name': _('Refund'),
                'quantity': 1,
                'price_unit': self.reverse_amount,
                'account_id': credit_note.journal_id.default_account_id.id,
            })
            credit_note._compute_amount()
        refund_request_id = self.env.context.get('refund_request_id')
        if refund_request_id and credit_note:
            self.env['education.refund.request'].browse(
                refund_request_id
            ).write({
                'credit_note_id': credit_note.id,
            })
        return res
