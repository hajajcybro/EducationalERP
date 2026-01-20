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
    active = fields.Boolean(default=True)
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
        ('transport','Transport payment'),
        ('hostel', 'Hostel Payment'),
    ],
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
    hostel_application_id = fields.Many2one(
        'education.hostel.application', string='Hostel Application',
        tracking=True
    )
    #scholarship manage
    apply_scholarship = fields.Boolean(
        string="Apply Scholarship",
        default=False
    )
    has_scholarship = fields.Boolean(
        compute="_compute_has_scholarship",
        store=False
    )
    scholarship_amount = fields.Float(
        compute="_compute_has_scholarship",
        store=False
    )
    scholarship_apply_type = fields.Selection([
        ('full', 'Use Full Scholarship Amount'),
        ('auto', 'Use Fee-wise Amount (Auto)'),
        ('partial', 'Use Partial Amount'),
    ], string="Scholarship Usage")

    scholarship_custom_amount = fields.Float(
        string="Scholarship Amount to Apply"
    )
    remaining_scholarship_amount = fields.Monetary(
        string="Remaining Scholarship Amount",
        compute="_compute_remaining_scholarship_amount",
    )

    @api.depends('invoice_ids.invoice_line_ids.price_subtotal')
    def _compute_total_invoiced_amount(self):
        """Compute the total invoiced amount for the record.
        This method sums the positive subtotal values of all invoice lines
        from non-cancelled invoices linked to the record. Discount or
        adjustment lines with negative amounts are excluded to ensure
        that only actual charge amounts are counted."""
        for rec in self:
            total = 0.0
            for inv in rec.invoice_ids.filtered(lambda m: m.state != 'cancel'):
                for line in inv.invoice_line_ids:
                    if line.price_subtotal > 0:
                        total += line.price_subtotal
            rec.total_invoiced_amount = total

    @api.depends('total_invoiced_amount')
    def _compute_remaining_amount(self):
        """Compute the remaining payable amount by subtracting the total invoiced amount
        from the related fee plan amount for the selected installment."""
        for rec in self:
            rec.remaining_amount = (
                rec.installment_id.fee_plan_id.amount - rec.total_invoiced_amount
                if rec.installment_id.fee_plan_id else 0.0
            )

    def action_create_invoice(self):
        """Create a customer invoice for the fee record based on the selected
        payment type.

        This method checks that the required setup is completed for the selected
        payment type (installment, full, transport, or hostel). It calculates the
        payable amount and prepares the invoice line details, then creates the
        customer invoice and links it to the fee record..

        If scholarship application is enabled, the method applies the approved
        scholarship as a negative invoice line based on the configured
        application type (full, automatic, or partial), ensuring that the
        available scholarship balance is not exceeded and updating the
        remaining scholarship amount accordingly.

        The method also evaluates applicable late payment penalty rules based
        on the invoice due date and applies penalties when the grace period
        is exceeded.
        """
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
        elif self.payment_type == 'hostel':
            application = self.hostel_application_id or self.env['education.hostel.application'].search([
                ('student_id', '=', self.student_id.id),], limit=1)
            allocate = application.allocation_detail_ids.filtered(
                lambda a: a.state == 'allocated')[:1]
            #for testing state change as draft because, in hostel management currently state is not declared
            hostel = allocate.hostel_id if allocate else False
            if not hostel:
                raise ValidationError(
                    _("No allocated hostel found for this student.")
                )
            price = (hostel.room_rent or 0.0) + (hostel.mess_fee or 0.0)
            line_name = 'Hostel & Food Fee'
            self.hide_invoice_button = False
        else:
            raise ValidationError(_("Please select a Payment Type."))
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
        # scholarship management
        if self.apply_scholarship and self.has_scholarship:
            application = self.env['education.scholarship.application'].search([
                ('student_id', '=', self.student_id.id),
                ('state', '=', 'approved'),
            ], limit=1)

            application.check_and_reset_scholarship()  #-<
            if not application or application.scholarship_remaining_amount <= 0:
                raise ValidationError(_("No remaining scholarship amount available."))
            if self.scholarship_apply_type == 'partial':
                if self.scholarship_custom_amount <= 0:
                    raise ValidationError(_("Scholarship amount must be greater than zero."))

                if self.scholarship_custom_amount > application.scholarship_remaining_amount:
                    raise ValidationError(_(
                        "Scholarship amount to apply cannot exceed the remaining scholarship balance."
                    ))
            discount = 0.0
            if self.scholarship_apply_type in ('full', 'auto'):
                discount = min(application.scholarship_remaining_amount, price)
            elif self.scholarship_apply_type == 'partial':
                discount = min(
                    self.scholarship_custom_amount,
                    application.scholarship_remaining_amount,
                    price
                )
            if discount > 0:
                scholarship_product = self.env['product.product'].search(
                    [('name', '=', 'Scholarship')], limit=1
                )
                invoice.write({
                    'invoice_line_ids': [
                        Command.create({
                            'product_id': scholarship_product.id,
                            'quantity': 1,
                            'price_unit': -discount,
                        })
                    ]
                })
                application.scholarship_remaining_amount -= discount

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
        if self.payment_type != 'hostel'  and self.remaining_amount <= 1:
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
        """Compute the total amount paid for the record.
        This method calculates the paid amount by summing the difference
        between the total and residual amounts of all posted invoices
        linked to the record."""
        for rec in self:
            paid = 0.0
            for inv in rec.invoice_ids.filtered(lambda m: m.state == 'posted'):
                paid += inv.amount_total - inv.amount_residual
            rec.amount_paid = paid

    @api.depends('invoice_ids.amount_residual')
    def _compute_outstanding_amount(self):
        """Compute the total outstanding amount for the record.
        This method sums the residual amounts of all posted invoices
        linked to the record to determine the outstanding balance."""
        for rec in self:
            rec.outstanding_amount = sum(
                rec.invoice_ids.filtered(lambda m: m.state == 'posted')
                .mapped('amount_residual')
            )

    @api.depends('invoice_ids.state', 'invoice_ids.move_type', 'invoice_ids.reversed_entry_id', 'invoice_ids.amount_total',)
    def _compute_reverse_amount(self):
        """Calculate the total refund amount associated with the record.
        The method identifies posted customer credit notes created as
        reversals of the record’s customer invoices and sums their total
        amounts to determine the reversed value."""
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
        """
        Compute the overall payment state based on related invoice states, payment type,
        and paid amount. Supports installment logic (not paid, partial, paid) and
        falls back to invoice payment states when applicable.
        """
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
        """Populate transport route, stop, and fee plan based on the selected student
        when the payment type is transport; otherwise reset transport fields."""
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

    def unlink(self):
        """Override unlink to log audit details before record deletion.
        Tracks deletion of records by capturing key business-relevant
        details for audit and compliance purposes.
        """
        for rec in self:
            old_data = {
                'Student': rec.student_id.display_name if rec.student_id else None,
                'Admission No': rec.admission_no,
                'Payment Type': rec.payment_type,
                'Fee Plan': rec.fee_plan_id.display_name if rec.fee_plan_id else None,
                'Total Invoiced Amount': rec.total_invoiced_amount,
                'Remaining Amount': rec.remaining_amount,
                'Due Date': rec.due_date,
                'Status': rec.status,
            }
            self.env['education.audit.log'].sudo().create({
                'user_id': self.env.user.id,
                'action_type': 'delete',
                'model_name': rec._name,
                'record_id': rec.id,
                'description': 'Record deleted',
                'old_values': old_data,
            })
        return super().unlink()

    @api.depends('student_id')
    def _compute_has_scholarship(self):
        """Check whether the selected student has any approved scholarship.
        If an approved scholarship application exists for the student,
        mark `has_scholarship` as True and set the scholarship amount.
        Otherwise, reset the values."""
        for rec in self:
            rec.has_scholarship = False
            rec.scholarship_amount = 0.0
            if rec.student_id:
                application = self.env['education.scholarship.application'].search([
                    ('student_id', '=', rec.student_id.id),('state', '=', 'approved'),
                ], limit=1)
                if application and application.scholarship_id.scholarship_amount > 0:
                    rec.has_scholarship = True
                    rec.scholarship_amount = application.scholarship_id.scholarship_amount

    @api.depends('student_id')
    def _compute_remaining_scholarship_amount(self):
        """ Compute the remaining scholarship amount for the record.
        The value is derived from the approved scholarship application
        linked to the selected student. If an approved application exists,
        the remaining scholarship balance from that application is assigned.
        If no student or approved application is found, the remaining
        scholarship amount is set to zero."""
        for rec in self:
            rec.remaining_scholarship_amount = 0.0
            if rec.student_id:
                application = self.env['education.scholarship.application'].search([
                    ('student_id', '=', rec.student_id.id),
                    ('state', '=', 'approved'),
                ], limit=1)
                if application:
                    rec.remaining_scholarship_amount = application.scholarship_remaining_amount
