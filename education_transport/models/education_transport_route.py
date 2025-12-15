# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError


class EduTransportRoute(models.Model):
    _name = 'education.transport.route'
    _description = 'Transport Route'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string="Route Name", required=True)
    # vehicle_id = fields.Many2one('education.transport.vehicle', string="Vehicle", required=True)
    vehicle_id = fields.Many2one('fleet.vehicle', string="Vehicle", required=True)
    stops = fields.One2many('education.transport.stop', 'route_id', string="Route Stops")
    active = fields.Boolean(string="Active", default=True)

    @api.constrains('vehicle_id', 'active')
    def _check_vehicle_already_assigned(self):
        """Ensure a vehicle is assigned to only one active route."""
        for route in self.filtered(lambda r: r.active and r.vehicle_id):
            conflict = self.search([
                ('id', '!=', route.id),
                ('vehicle_id', '=', route.vehicle_id.id),
                ('active', '=', True),
            ], limit=1)
            if conflict:
                raise ValidationError(
                    f"Vehicle '{route.vehicle_id.reg_no}' is already "
                    f"active in route '{conflict.name}'."
                )
