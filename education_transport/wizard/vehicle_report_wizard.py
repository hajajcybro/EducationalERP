# -*- coding: utf-8 -*-
from odoo import models, fields

class TransportVehicleWizard(models.TransientModel):
    _name = 'transport.vehicle.wizard'
    _description = 'Transport Vehicle Wizard'

    vehicle_ids = fields.Many2many(
        'fleet.vehicle',
        string="Vehicles",
        domain=[('is_transport_vehicle', '=', True)],
        help="Select one or more vehicles for detailed report"
    )

    report_type = fields.Selection([
        ('over', 'Over-Occupied Vehicles'),
        ('available', 'Available Vehicles'),
    ], string="Report Type",
        help="Used when no vehicle is selected")

    def action_pdf_print(self):
        data = {
            'report_type': self.report_type,
            'vehicle_ids': self.vehicle_ids.ids,
        }
        print(data)
        return self.env.ref('education_transport.action_report_vehicle_information').report_action(None, data=data)

