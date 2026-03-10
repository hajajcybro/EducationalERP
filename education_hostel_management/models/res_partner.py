# -*- coding: utf-8 -*-

from odoo import models, fields


class ResPartner(models.Model):
    _inherit = 'res.partner'

    hostel = fields.Boolean( string='Need Hostel Facility',
        help='True if partner needs a hostel facility'
    )
