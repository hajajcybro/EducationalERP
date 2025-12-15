# -*- coding: utf-8 -*-
from odoo import models, fields, api


class TransportDelayWizard(models.TransientModel):
    _name = 'transport.delay.wizard'
    _description = 'Transport Delay Notification Wizard'

    route_id = fields.Many2one('education.transport.route', required=True)
    delay_minutes = fields.Integer(required=True)
    delay_reason = fields.Text(required=True)

    def action_send_notifications(self):
        """Send notifications"""
        print('ghkj')



