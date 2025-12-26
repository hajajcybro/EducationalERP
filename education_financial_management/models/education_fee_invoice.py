# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


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

    invoice_id = fields.Many2one(
        'account.move',
        string='Invoice',
        ondelete='cascade'
    )

    status = fields.Selection(
        [('draft', 'Draft'),('posted', 'Posted'),('paid', 'Paid'),('cancelled', 'Cancelled')],
        string='Status',
        default='draft',
        tracking=True
    )
    remarks = fields.Text(string='Remarks')
    currency_id = fields.Many2one(
        related='invoice_id.currency_id',
        store=True,
        readonly=True
    )

    amount_total = fields.Monetary(
        related='invoice_id.amount_total',
        string='Total Amount',
        store=True,
        readonly=True
    )
    payment_type= fields.Selection([('installment', 'Installment'),('full', 'Full Payment')],
        string="Installment",
        default=False)

    def action_create_invoice(self):
        """Open customer invoice form with defaults."""
        print('invoice button')
        self.ensure_one()

        price = (
            self.installment_id.amount
            if self.installment_id
            else self.fee_plan_id.amount
        )
        currency_id = (
                self.fee_plan_id.currency_id.id
                or self.env.company.currency_id.id
        )

        return {
            'type': 'ir.actions.act_window',
            'name': _('Create Invoice'),
            'res_model': 'account.move',
            'view_mode': 'form',
            'target': 'current',
            'context': {
                'default_move_type': 'out_invoice',
                'default_partner_id': self.student_id.id,
                'default_currency_id': currency_id,

                'default_invoice_line_ids': [
                    (0, 0, {
                        'product_id': self.fee_plan_id.product_id.id,
                        'name': self.fee_plan_id.name,
                        'quantity': 1,
                        'price_unit': price,
                    })
                ],
            }
        }

