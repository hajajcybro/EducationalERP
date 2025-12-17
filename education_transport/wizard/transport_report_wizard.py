# -*- coding: utf-8 -*-
from odoo import models, fields
import io
import json
import xlsxwriter
from odoo.tools import json_default, Query
from odoo.tools.parse_version import replace

class TransportReportWizard(models.TransientModel):
    """create model for manage leaves"""
    _name = 'transport.report.wizard'
    _description = 'Transport Report Wizard'

    report_type = fields.Selection([
        ('route', 'Route-wise Student Report'),
        ('vehicle', 'Vehicle Wise Report'),
    ], string="Report Type", required=True, default='route')
    route_id = fields.Many2one(
        'education.transport.route',
        string="Route",
        help="Select route for route-wise report"
    )
    vehicle_id = fields.Many2one(
        'fleet.vehicle',
        string="Vehicle",
        domain=[('is_transport_vehicle', '=', True)],
        help="Select vehicle for occupancy report"
    )

    def action_print_report(self):
        data = {
            'report_type': self.report_type,
            'route_id': self.route_id.id,
            'vehicle_id': self.vehicle_id.id,
        }
        print(data)
        return self.env.ref('education_transport.action_report_transport_information').report_action(None, data=data)



    def action_generate_leave_xl_report(self):
        """Button action for generate xlxs report"""
        data = {
            'model_id': 'transport.report.wizard',
            'report_type': self.report_type,
            'route_id': self.route_id.id,
            'vehicle_id': self.vehicle_id,
        }
        print("xlxs 1st")
        return {
            'type': 'ir.actions.report',
            'data': {'model': 'transport.report.wizard',
                     'options': json.dumps(data, default=json_default),
                     'output_format': 'xlsx',
                     'report_name': 'student Transport Report',
                     },
            'report_type': 'xlsx',
        }

    def get_xlsx_report(self, data, response):
        params = []
        query = """SELECT rp.name AS student_name,
                           r.name AS route_name,
                           s.stop_name,
                           s.pickup_time,
                           s.drop_time
                   FROM education_transport_assignment a
                   JOIN res_partner rp ON rp.id = a.student_id
                   JOIN education_transport_route r ON r.id = a.route_id
                   JOIN education_transport_stop s ON s.id = a.stop_id
                   WHERE a.active = TRUE
               """

        # Route filter
        if data.get('report_type') == 'route' and data.get('route_id'):
            query += " AND a.route_id = %s"
            params.append(data['route_id'])

        # Vehicle filter
        if data.get('report_type') == 'vehicle' and data.get('vehicle_id'):
            query += " AND r.vehicle_id = %s"
            params.append(data['vehicle_id'])

        query += " ORDER BY r.name, s.sequence"

        self.env.cr.execute(query, params)
        records = self.env.cr.dictfetchall()

        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet('Transport Report')

        header = workbook.add_format({'bold': True, 'align': 'center'})
        text = workbook.add_format({'align': 'center'})
        sheet.set_column('A:A', 18)
        sheet.set_column('B:B', 15)
        sheet.set_column('C:C', 15)
        sheet.set_column('D:E', 12)

        # Headers
        headers = ['Student', 'Route', 'Stop', 'Pickup Time', 'Drop Time']
        for col, h in enumerate(headers):
            sheet.write(0, col, h, header)

        # Data rows
        row = 1
        for rec in records:
            sheet.write(row, 0, rec['student_name'], text)
            sheet.write(row, 1, rec['route_name'], text)
            sheet.write(row, 2, rec['stop_name'], text)
            sheet.write(row, 3, rec['pickup_time'], text)
            sheet.write(row, 4, rec['drop_time'], text)
            row += 1

        workbook.close()
        output.seek(0)

        # STREAM RESPONSE
        response.stream.write(output.read())
        output.close()

