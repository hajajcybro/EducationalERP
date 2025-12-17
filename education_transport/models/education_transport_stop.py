# -*- coding: utf-8 -*-
from odoo import models, fields,api,_
from odoo.exceptions import ValidationError



class EduTransportStop(models.Model):
    _name = 'education.transport.stop'
    _description = 'Transport Route Stop'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'stop_name'
    _order = 'route_id'

    route_id = fields.Many2one('education.transport.route', string="Route")
    stop_name = fields.Char(string="Stop Name", required=True)
    sequence = fields.Integer(string="Sequence")
    pickup_time = fields.Float(string='Pickup Time', required=True)
    drop_time = fields.Float(string='Drop Time', required=True)

    @api.constrains('pickup_time', 'drop_time')
    def _check_pickup_drop_time(self):
        """Validate that the drop time is later than the pickup time."""
        for record in self:
            if record.pickup_time and record.drop_time:
                if record.drop_time <= record.pickup_time:
                    raise ValidationError(
                        'Drop time must be later than pickup time on the same day.'
                    )

    @api.onchange('route_id')
    def _onchange_route_id_set_sequence(self):
        """ Auto-assign the next sequence number based on the selected route."""
        if self.route_id:
            last_stop = self.search(
                [('route_id', '=', self.route_id.id)],
                order='sequence desc',
                limit=1
            )
            self.sequence = (last_stop.sequence + 1) if last_stop else 1

    @api.constrains('route_id', 'pickup_time', 'drop_time')
    def _check_duplicate_times_per_route(self):
        """Prevent duplicate pickup or drop times for stops within the same route."""
        for record in self:
            # Check duplicate pickup time
            pickup_conflict = self.search([
                ('id', '!=', record.id),
                ('route_id', '=', record.route_id.id),
                ('pickup_time', '=', record.pickup_time),
            ], limit=1)
            if pickup_conflict:
                raise ValidationError(
                    _("Pickup time %.2f is already assigned to stop '%s' in route '%s'.")
                    % (record.pickup_time, pickup_conflict.stop_name, record.route_id.name)
                )
            # Check duplicate drop time
            drop_conflict = self.search([
                ('id', '!=', record.id),
                ('route_id', '=', record.route_id.id),
                ('drop_time', '=', record.drop_time),
            ], limit=1)
            if drop_conflict:
                raise ValidationError(
                    _("Drop time %.2f is already assigned to stop '%s' in route '%s'.")
                    % (record.drop_time, drop_conflict.stop_name, record.route_id.name)
                )

    @api.constrains('route_id', 'stop_name')
    def _check_unique_stop_per_route(self):
        """
        Prevent duplicate stop names within the same route.
        Same stop name is allowed across different routes.
        """
        for record in self:
            conflict = self.search([
                ('id', '!=', record.id),
                ('route_id', '=', record.route_id.id),
                ('stop_name', '=', record.stop_name),
            ], limit=1)
            if conflict:
                raise ValidationError(
                    _("Stop '%s' is already defined for route '%s'.")
                    % (record.stop_name, record.route_id.name)
                )

