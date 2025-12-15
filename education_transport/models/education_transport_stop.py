# -*- coding: utf-8 -*-
from odoo import models, fields,api
from odoo.exceptions import ValidationError



class EduTransportStop(models.Model):
    _name = 'education.transport.stop'
    _description = 'Transport Route Stop'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'stop_name'

    route_id = fields.Many2one('education.transport.route', string="Route")
    stop_name = fields.Char(string="Stop Name", required=True)
    sequence = fields.Integer(string="Sequence")
    pickup_time = fields.Float(string='Pickup Time', required=True)
    drop_time = fields.Float(string='Drop Time', required=True)

    @api.constrains('pickup_time', 'drop_time')
    def _check_pickup_drop_time(self):
        for record in self:
            if record.pickup_time and record.drop_time:
                if record.drop_time <= record.pickup_time:
                    raise ValidationError(
                        'Drop time must be later than pickup time on the same day.'
                    )

