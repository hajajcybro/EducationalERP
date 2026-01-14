# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class EducationRefundRequest(models.Model):
    _name = 'education.refund.request'
    _description = 'Education Refund Request'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name='student_id'

    student_id = fields.Many2one(
        'res.partner',
        string='Student',domain=[('is_student', '=', True)],
        required=True,
        tracking=True
    )
    invoice_id = fields.Many2one(
        'account.move',
        string='Invoice',
        required=True,
        domain=[('move_type', '=', 'out_invoice'),
                ('fee_invoice_id.active', '=', True)],
        tracking=True
    )
    currency_id = fields.Many2one(
        'res.currency',
        related='invoice_id.currency_id',
        store=True,
        readonly=True
    )
    refund_amount = fields.Monetary(
        string='Refund Amount',
        required=True,
        tracking=True
    )
    reason = fields.Text(
        string='Reason',
        required=True
    )
    state = fields.Selection([
        ('draft', 'Draft'),
        ('approved', 'Approved'),
        ('processed', 'Processed'),
        ('reversed', 'Reversed'),
        ('rejected', 'Rejected'),
    ], default='draft', tracking=True)
    processed_by = fields.Many2one(
        'res.users',
        string='Processed By',
        readonly=True
    )
    processed_date = fields.Date(
        string='Processed Date',
        readonly=True
    )
    rejection_reason = fields.Text(
        string="Rejection Reason",
        readonly=True,
        tracking=True
    )
    credit_note_id = fields.Many2one(
        'account.move',
        string="Credit Note",
        compute='_compute_credit_note',
        readonly=True
    )

    @api.constrains('refund_amount', 'invoice_id')
    def _check_refund_amount(self):
        """ Validate refund requests to ensure the amount is positive,
        Invoice must belong to selected student,
        the related invoice is fully paid, and the refund does not
        exceed the invoice total."""
        for rec in self:
            if rec.student_id and rec.invoice_id:
                if rec.invoice_id.partner_id != rec.student_id:
                    raise ValidationError(
                        _("The selected invoice does not belong to the chosen student.")
                    )
            if rec.refund_amount <= 0:
                raise ValidationError(_("Refund amount must be greater than zero."))
            if rec.invoice_id:
                if rec.invoice_id.payment_state != 'paid':
                    raise ValidationError(
                        _("Refund can only be requested for paid invoices.")
                    )
                if rec.invoice_id.status_in_payment == 'reversed':
                    raise ValidationError(
                        _("Already refund with this invoice.")
                    )
                if rec.refund_amount > rec.invoice_id.amount_total:
                    raise ValidationError(
                        _("Refund amount cannot exceed the invoice total.")
                    )

    def action_approve(self):
        """ Mark the refund request as approved."""
        for rec in self:
            rec.state = 'approved'

    def action_reject(self):
        """Open rejection wizard to capture rejection reason."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Reject Refund Request'),
            'res_model': 'education.refund.reject.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_refund_request_id': self.id,
            }
        }

    def action_processed(self):
        """ Mark refund request as processed and allow invoice-level refund actions."""
        for rec in self:
            rec.write({
                'state': 'processed',
                'processed_by': self.env.user.id,
                'processed_date': fields.Date.today(),
            })

    def action_open_invoice(self):
        """ Open the related invoice for refund processing."""
        print('open invoice')
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Invoice'),
            'res_model': 'account.move',
            'view_mode': 'form',
            'res_id': self.invoice_id.id,
            'target': 'current',
            'context': {
                'refund_request_id': self.id
            }
        }

    @api.depends('invoice_id', 'invoice_id.payment_state')
    def _compute_credit_note(self):
        """ Compute the related credit note for the refund request and
        synchronize the refund state based on the credit note status.
        - If a draft credit note exists, link it and keep the refund
          request in 'processed' state.
        - If the credit note is posted, link it and update the refund
          request to 'reversed' state."""
        for rec in self:
            rec.credit_note_id = False
            credit_note = self.env['account.move'].search([
                ('move_type', '=', 'out_refund'),
                ('reversed_entry_id', '=', rec.invoice_id.id),
            ], limit=1)
            if credit_note:
                rec.credit_note_id = credit_note
                if credit_note.state == 'posted':
                    rec.state = 'reversed'
                else:
                    rec.state = 'processed'






