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
        domain=[('move_type', '=', 'out_invoice')],
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
        ('rejected', 'Rejected'),
        ('processed', 'Processed'),
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

    @api.constrains('refund_amount')
    def _check_refund_amount(self):
        for rec in self:
            if rec.refund_amount <= 0:
                raise ValidationError(_("Refund amount must be greater than zero."))

            if rec.invoice_id and rec.refund_amount > rec.invoice_id.amount_total:
                raise ValidationError(_("Refund amount cannot exceed the invoice total."))
