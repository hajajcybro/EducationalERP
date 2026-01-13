# -*- coding: utf-8 -*-
from odoo import models, fields, api

class EducationTransportFee(models.Model):
    _name = 'education.transport.fee'
    _description = 'Transport Fee Rule'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(required=True)
    route_id = fields.Many2one('education.transport.route', required=True)
    stop_ids = fields.Many2many('education.transport.stop','stop_name')
    amount = fields.Float(required=True)
    currency_id = fields.Many2one(
        'res.currency', default=lambda self: self.env.company.currency_id
    )
    product_id = fields.Many2one('product.product', readonly=True)

    @api.model
    def create(self, vals):
        """
        Create a transport fee record and automatically create or link a
        corresponding service product based on the route and stops.
        """
        fee = super().create(vals)
        ProductTemplate = self.env['product.template']
        print(fee.stop_ids.read())
        name = f"Transport Fee - {fee.route_id.name}"
        if fee.stop_ids:
            name += f" ({', '.join(fee.stop_ids.mapped('display_name'))})"
        product_tmpl = ProductTemplate.search([
            ('name', '=', name),
            ('type', '=', 'service'),
        ], limit=1)
        if not product_tmpl:
            product_tmpl = ProductTemplate.create({
                'name': name,
                'type': 'service',
                'list_price': fee.amount,
                'currency_id': fee.currency_id.id,
            })
        fee.product_id = product_tmpl.product_variant_id.id
        return fee

