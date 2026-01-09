# -*- coding: utf-8 -*-
from odoo import models, fields, api, _,Command
from odoo.exceptions import ValidationError
from datetime import timedelta

class EduFeeInvoice(models.Model):
    _name = 'education.fee.invoice'
    _description = 'Education Fee Invoice'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'student_id'

    student_id = fields.Many2one(
        'res.partner',
        string='Student',domain=[('is_student', '=', True)],
        required=True,
        tracking=True
    )
    admission_no = fields.Char(related='student_id.admission_no', string="Register No")
    enrollment_id = fields.Many2one(
        'education.enrollment',
        string='Enrollment',
        tracking=True
    )
    fee_plan_id = fields.Many2one(
        'education.fee.plan',
        string='Fee Plan',
        tracking=True
    )
    installment_id = fields.Many2one(
        'education.fee.installment',
        string='Installment Plan'
    )
    status = fields.Selection(
        [('draft', 'Draft'),('posted', 'Posted'),('paid', 'Paid'),('cancelled', 'Cancelled')],
        string='Status',
        store=True,
        tracking=True,
    )
    remarks = fields.Text(string='Remarks')
    currency_id = fields.Many2one(
        'res.currency',
        default=lambda self: self.env.company.currency_id
    )
    payment_type= fields.Selection([
        ('installment', 'Installment'),
        ('full', 'Full Amount'),
        ('transport','Transport payment')],
        string="Payment Type",
        default=False)
    due_date = fields.Date(string='Due Date')
    invoice_ids = fields.One2many(
        'account.move',
        'fee_invoice_id',
        string='Invoices',
        readonly=True
    )
    payment_term_id = fields.Many2one(
        'account.payment.term',
        string='Payment Terms'
    )
    hide_invoice_button = fields.Boolean(
        string='Hide Invoice Button',
        copy=False
    )
    total_invoiced_amount = fields.Monetary(
        compute='_compute_total_invoiced_amount',
        store=True
    )
    remaining_amount = fields.Monetary(
        compute='_compute_remaining_amount',
        store=True,
        string='Installment Remaining Amount'
    )
    amount_paid = fields.Monetary(
        compute='_compute_amount_paid',
        store=True,
        string='Amount Paid'
    )
    outstanding_amount = fields.Monetary(
        compute='_compute_outstanding_amount',
        store=True,
        string='Outstanding Amount'
    )
    reverse_amount = fields.Monetary(
        compute='_compute_reverse_amount',
        store=True,
        string='Refunded Amount'
    )
    payment_state = fields.Selection(
        [('not_paid', 'Not Paid'),('partial', 'Partially Paid'), ('paid', 'Paid')],
        compute='_compute_payment_state',
        store=True,
        readonly=True,
        tracking=True
    )
    route_id = fields.Many2one(
        'education.transport.route', string='Route',readonly='True'
    )
    stop_id = fields.Many2one(
        'education.transport.stop', string='Stop',readonly='True'
    )
    transport_plan_id = fields.Many2one('education.transport.fee','Transport Plan')

    @api.depends('invoice_ids.amount_total')
    def _compute_total_invoiced_amount(self):
        for rec in self:
            rec.total_invoiced_amount = sum(rec.invoice_ids.mapped('amount_total'))

    @api.depends('total_invoiced_amount')
    def _compute_remaining_amount(self):
        for rec in self:
            rec.remaining_amount = (
                rec.installment_id.fee_plan_id.amount - rec.total_invoiced_amount
                if rec.installment_id.fee_plan_id else 0.0
            )

    def action_create_invoice(self):
        self.ensure_one()
        if self.payment_type == 'installment':
            if not self.installment_id:
                raise ValidationError(_("Please select an Installment Plan."))
            price = self.installment_id.installment_amount
            line_name = self.installment_id.name
        elif self.payment_type == 'full':
            if not self.fee_plan_id:
                raise ValidationError(_("Please select a Fee Plan."))
            price = self.fee_plan_id.amount
            line_name = self.fee_plan_id.name
            self.hide_invoice_button = True
        elif self.payment_type == 'transport':
            price = self.transport_plan_id.amount
            line_name = self.transport_plan_id.name
            self.hide_invoice_button = True

        invoice = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.student_id.id,
            'invoice_date': fields.Date.today(),
            'invoice_date_due': self.due_date or fields.Date.today(),
            'fee_invoice_id': self.id,
            'invoice_payment_term_id': self.payment_term_id.id,
            'invoice_line_ids': [Command.create({
                'name': line_name,
                'quantity': 1,
                'price_unit': price,
            })],
        })
        rule = False
        if self.payment_type == 'installment':
            rule = self.installment_id.penalty_rule_id
        elif self.payment_type == 'full':
            rule = self.fee_plan_id.penalty_rule_id
        if rule and rule.product_id and invoice.invoice_date_due:
            today = fields.Date.today()
            penalty_start = invoice.invoice_date_due + timedelta(days=rule.grace_period)
            if today > penalty_start:
                late_days = (today - penalty_start).days
                if late_days > 0:
                    if rule.penalty_type == 'fixed':
                        unit_price = rule.value
                    else:
                        unit_price = (invoice.amount_untaxed * rule.value) / 100
                        print(unit_price)
                    invoice.write({
                        'invoice_line_ids': [
                            Command.create({
                                'product_id': rule.product_id.id,
                                'name': f'{rule.name} ({late_days} days late)',
                                'quantity': late_days,
                                'price_unit': unit_price,
                            })
                        ]
                    })
        self.write({'invoice_ids': [Command.link(invoice.id)]})
        if self.remaining_amount <= 1:
            self.hide_invoice_button = True
        return {
            'type': 'ir.actions.act_window',
            'name': 'Invoice',
            'res_model': 'account.move',
            'res_id': invoice.id,
            'view_mode': 'form',
            'target': 'current',
        }

    @api.depends('invoice_ids.amount_total', 'invoice_ids.amount_residual')
    def _compute_amount_paid(self):
        for rec in self:
            paid = 0.0
            for inv in rec.invoice_ids.filtered(lambda m: m.state == 'posted'):
                paid += inv.amount_total - inv.amount_residual
            rec.amount_paid = paid

    @api.depends('invoice_ids.amount_residual')
    def _compute_outstanding_amount(self):
        for rec in self:
            rec.outstanding_amount = sum(
                rec.invoice_ids.filtered(lambda m: m.state == 'posted')
                .mapped('amount_residual')
            )

    @api.depends('invoice_ids.state', 'invoice_ids.move_type', 'invoice_ids.reversed_entry_id', 'invoice_ids.amount_total',)
    def _compute_reverse_amount(self):
        for rec in self:
            refund_total = 0.0
            invoices = rec.invoice_ids.filtered(
                lambda m: m.move_type == 'out_invoice'
            )
            credit_notes = self.env['account.move'].search([
                ('move_type', '=', 'out_refund'),
                ('state', '=', 'posted'),
                ('reversed_entry_id', 'in', invoices.ids),
            ])
            refund_total = sum(credit_notes.mapped('amount_total'))
            rec.reverse_amount = refund_total

    @api.depends('invoice_ids.payment_state', 'amount_paid', 'total_invoiced_amount','payment_type')
    def _compute_payment_state(self):
        for rec in self:
            states = rec.invoice_ids.mapped('payment_state')
            if not states:
                rec.payment_state = 'not_paid'
            if rec.payment_type == 'installment':
                if rec.amount_paid == 0:
                    rec.payment_state = 'not_paid'
                elif rec.amount_paid < rec.total_invoiced_amount:
                    rec.payment_state = 'partial'
                else:
                    rec.payment_state = 'paid'
            if all(state == 'paid' for state in states):
                rec.payment_state = 'paid'
            else:
                rec.payment_state = 'not_paid'

    @api.onchange('student_id', 'payment_type')
    def _onchange_student_transport_payment(self):
        if not self.student_id or self.payment_type != 'transport':
            self.route_id = self.stop_id = False
            return
        assignment = self.env['education.transport.assignment'].search([
            ('student_id', '=', self.student_id.id),
            ('active', '=', True),
        ], limit=1)
        if assignment:
            self.route_id = assignment.route_id
            self.stop_id = assignment.stop_id
            self.transport_plan_id = self.env['education.transport.fee'].search([
                ('route_id', '=', assignment.route_id.id),
                ('stop_ids', 'in', assignment.stop_id.id),
            ], limit=1)
        else:
            self.route_id = self.stop_id = False


