# -*- coding: utf-8 -*-
from odoo import models, fields

class EduTransportVehicle(models.Model):
    _name = 'education.transport.vehicle'
    _description = 'Transport Vehicle'
    _rec_name = 'reg_no'

    reg_no = fields.Char(string="Registration Number", required=True)
    capacity = fields.Integer(string="Capacity", required=True)
    driver_id = fields.Many2one('res.partner', string="Driver")
    status = fields.Selection([
        ('active', 'Active'),
        ('maintenance', 'Under Maintenance'),
        ('inactive', 'Inactive'),
    ], string="Status", default='active', required=True)
''