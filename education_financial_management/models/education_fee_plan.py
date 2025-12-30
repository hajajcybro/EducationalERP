# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError



class EduFeePlan(models.Model):
    _name = 'education.fee.plan'
    _description = 'Fee Plan'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'academic_year_id desc, name'

    name = fields.Char(
        string='Fee Plan Name',
        required=True,
        tracking=True,
        help='Name of the fee plan.'
    )
    program_id = fields.Many2one(
        'education.program',
        string='Program',
        tracking=True
    )
    academic_year_id = fields.Many2one(
        'education.academic.year',
        string='Academic Year',
        tracking=True
    )
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        required=True,
        default=lambda self: self.env.company.currency_id
    )

    installment_ids = fields.One2many(
        'education.fee.installment',
        'fee_plan_id',
        string='Installments'
    )
    amount = fields.Float(
        string='Amount',
        store=True,
    )

    product_id = fields.Many2one(
        'product.product',
        string='Fee Product',
        readonly=True,
        copy=False
    )
    penalty_rule_id = fields.Many2one(
        'education.fee.penalty.rule',
        string='Penalty Rule'
    )

    notes = fields.Text(string='Notes')

    active = fields.Boolean(default=True)

    @api.constrains('program_id', 'academic_year_id')
    def _check_duration_match(self):
        """Ensure program duration matches academic year duration."""
        for rec in self:
            if rec.program_id and rec.academic_year_id:
                program_duration = rec.program_id.duration or 0.0
                year_duration = rec.academic_year_id.duration or 0.0
                if float(program_duration) != float(year_duration):
                    raise ValidationError(_(
                        "Duration mismatch: The selected program (%s years) "
                        "does not match the academic year (%s years)."
                    ) % (program_duration, year_duration))

    @api.constrains('amount')
    def _check_amount(self):
        """ Validate that the fee amount is a positive value."""
        for rec in self:
            if rec.amount <= 0:
                raise ValidationError("Fee amount must be greater than zero.")

    @api.constrains('program_id', 'academic_year_id')
    def _check_unique_plan(self):
        """    Ensure only one fee plan exists per program and academic year."""
        for rec in self:
            domain = [
                ('id', '!=', rec.id),
                ('program_id', '=', rec.program_id.id),
                ('academic_year_id', '=', rec.academic_year_id.id),
            ]
            if self.search_count(domain):
                raise ValidationError(
                    "A fee plan already exists for this Program and Academic Year."
                )

    @api.model
    def create(self, vals):
        """Automatically creates or links a service product for the fee plan."""
        plan = super().create(vals)

        ProductTemplate = self.env['product.template']
        product_tmpl = ProductTemplate.search([
            ('name', '=', plan.name),
            ('type', '=', 'service'),
        ], limit=1)
        if not product_tmpl:
            product_tmpl = ProductTemplate.create({
                'name': plan.name,
                'type': 'service',
                'list_price': plan.amount,
                'currency_id': plan.currency_id.id,
            })
        # Link the single variant
        plan.product_id = product_tmpl.product_variant_id.id

        return plan

