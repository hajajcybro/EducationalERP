# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class EducationFeePenaltyRule(models.Model):
    _name = 'education.fee.penalty.rule'
    _description = 'Education Fee Penalty Rule'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name'

    name = fields.Char(
        string='Penalty Rule Name',
        required=True,
        tracking=True
    )
    penalty_type = fields.Selection(
        [('fixed', 'Fixed Amount'), ('percentage', 'Percentage'),],
        string='Penalty Type',
        required=True,
        default='fixed',
        tracking=True
    )
    value = fields.Float(
        string='Penalty Value',
        required=True,
        tracking=True,
        help="Fixed amount or percentage value based on penalty type."
    )
    grace_period = fields.Integer(
        string='Grace Period (Days)',
        default=0,
        help="Number of days after due date before penalty applies."
    )
    active = fields.Boolean(
        default=True
    )
    product_id = fields.Many2one(
        'product.product',
        string='Penalty Product',
        readonly=True,
        copy=False
    )

    @api.constrains('value')
    def _check_value(self):
        """Validate penalty value based on penalty type."""
        for rule in self:
            if rule.value <= 0:
                raise ValidationError(_("Penalty value must be greater than zero."))

    @api.model
    def create(self, vals):
        """Create a penalty rule and automatically link a corresponding service product.
        Ensures a unique penalty product is created or reused for invoice penalties. """
        rule = super().create(vals)
        Product = self.env['product.product']
        price = rule.value if rule.penalty_type == 'fixed' else 0.0
        product = Product.search([
            ('default_code', '=', f'PENALTY-{rule.id}')
        ], limit=1)
        if not product:
            product = Product.create({
                'name': rule.name,
                'type': 'service',
                'list_price': price,
                'standard_price': price,
                'default_code': f'PENALTY-{rule.id}',
            })
        rule.product_id = product.id
        return rule




