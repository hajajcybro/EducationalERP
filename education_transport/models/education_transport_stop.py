# -*- coding: utf-8 -*-
from odoo import models, fields

class EduTransportStop(models.Model):
    _name = 'education.transport.stop'
    _description = 'Transport Route Stop'
    _order = 'sequence asc'

    route_id = fields.Many2one('education.transport.route', string="Route")
    stop_name = fields.Char(string="Stop Name", required=True)
    sequence = fields.Integer(string="Sequence")
    pickup_time = fields.Datetime(string="Pickup Time")
    drop_time = fields.Datetime(string="Drop Time")
