# -*- coding: utf-8 -*-
from odoo import models, fields, api

class EduFeeInstallment(models.Model):
    _name = 'education.fee.installment'
    _description = 'Fee Installment'
    _inherit = ['mail.thread', 'mail.activity.mixin']


    fee_plan_id = fields.Many2one(
        'education.fee.plan',
        string='Fee Plan',
        required=True,
        ondelete='cascade'
    )
    name = fields.Char(
        string='Installment Name',
        required=True
    )
    amount = fields.Float(
        string='Amount',
        related='fee_plan_id.amount',
        store=True,
        readonly=True
    )
    duration = fields.Integer('Duration')
    currency_id = fields.Many2one(
        related='fee_plan_id.currency_id',
        store=True,
        readonly=True
    )
    installment_amount = fields.Float(
        string='Installment Amount',
        compute='_compute_installment_amount',
        store=True
    )
    penalty_rule_id = fields.Many2one(
        'education.fee.penalty.rule',
        string='Penalty Rule'
    )

    product_id = fields.Many2one(
        'product.product',
        string='Installment Product',
        readonly=True,
        copy=False
    )


    @api.depends('fee_plan_id.amount', 'duration')
    def _compute_installment_amount(self):
        """ Calculate installment amount based on total fee and duration."""
        for rec in self:
            if rec.duration and rec.fee_plan_id.amount:
                rec.installment_amount = rec.fee_plan_id.amount / rec.duration

    @api.model
    def create(self, vals):
        installment = super().create(vals)
        Product = self.env['product.product']
        product_name =f"{installment.name} – Installment"
        # Check if product already exists
        product = Product.search([
            ('name', '=', product_name),
            ('default_code', '=', f"INST-{installment.id}")
        ], limit=1)
        if not product:
            product = Product.create({
                'name': product_name,
                'type': 'service',
                'list_price': installment.installment_amount,
                'standard_price': installment.installment_amount,
                'currency_id': installment.currency_id.id,
                'default_code': f"INST-{installment.id}",
            })
        installment.product_id = product.id
        return installment
