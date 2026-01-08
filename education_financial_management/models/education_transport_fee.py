# -*- coding: utf-8 -*-
from odoo import models, fields


class EducationTransportFee(models.Model):
    _name = 'education.transport.fee'
    _description = 'Transport Fee Rule'

    route_id = fields.Many2one('education.transport.route', required=True)
    stop_id = fields.Many2one('education.transport.stop')
    amount = fields.Float(required=True)
    currency_id = fields.Many2one(
        'res.currency',
        default=lambda self: self.env.company.currency_id
    )
    product_id = fields.Many2one('product.product', readonly=True)
