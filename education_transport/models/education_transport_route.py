# -*- coding: utf-8 -*-
from odoo import models, fields

class EduTransportRoute(models.Model):
    _name = 'education.transport.route'
    _description = 'Transport Route'

    name = fields.Char(string="Route Name", required=True)
    vehicle_id = fields.Many2one('education.transport.vehicle', string="Vehicle", required=True)
    stops = fields.One2many('education.transport.stop', 'route_id', string="Route Stops")
    active = fields.Boolean(string="Active", default=True)

