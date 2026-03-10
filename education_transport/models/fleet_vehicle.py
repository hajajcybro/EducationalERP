# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError

class FleetVehicle(models.Model):
    _inherit = 'fleet.vehicle'

    is_transport_vehicle = fields.Boolean(
        string="Used for Transport",
    )
    empl_driver_id = fields.Many2one('hr.employee', string="Driver", domain =[('role', '=', 'driver')],required = True)
    reg_no = fields.Char(string="Registration Number", required=True)
    capacity = fields.Integer(string="Capacity", required=True)
    status = fields.Selection([
        ('active', 'Active'),
        ('maintenance', 'Under Maintenance'),
        ('inactive', 'Inactive'),
    ], string="Status", default='active', required=True)

    @api.constrains('capacity')
    def _check_capacity(self):
        """Ensure that the vehicle capacity is a positive value."""
        for record in self:
            if record.capacity <= 0:
                raise ValidationError('Vehicle capacity must be greater than zero.')

    @api.constrains('driver_id', 'status')
    def _check_driver_already_assigned(self):
        """Ensure a driver is assigned to only one active vehicle."""
        for vehicle in self.filtered(lambda v: v.driver_id and v.status == 'active'):
            conflict = self.search([
                ('id', '!=', vehicle.id),
                ('driver_id', '=', vehicle.driver_id.id),
                ('status', '=', 'active'),
            ], limit=1)
            if conflict:
                raise ValidationError(
                    f"Driver '{vehicle.driver_id.name}' is already assigned to "
                    f"vehicle '{conflict.reg_no}'."
                )

    def action_maintenance(self):
        """    Mark the vehicle as under maintenance."""
        self.write({'status': 'maintenance'})

    def action_inactive(self):
        """    Deactivate the vehicle."""
        self.write({'status': 'inactive'})

