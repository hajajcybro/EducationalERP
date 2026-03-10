# -*- coding: utf-8 -*-
from odoo import models, fields
import io
import json
import xlsxwriter
from odoo.tools import json_default

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


    def action_generate_xl_report(self):
        """Button action for generate xlxs report"""
        data = {
            'model_id': 'transport.vehicle.wizard',
            'report_type': self.report_type,
            'vehicle_ids': self.vehicle_ids.ids,
        }
        return {
            'type': 'ir.actions.report',
            'data': {'model': 'transport.vehicle.wizard',
                     'options': json.dumps(data, default=json_default),
                     'output_format': 'xlsx',
                     'report_name': 'Vehicle Report',
                     },
            'report_type': 'xlsx',
        }

    def get_xlsx_report(self, data, response):
        """Generate Vehicle Occupancy XLSX report"""

        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet('Vehicles')

        # Formats
        title = workbook.add_format({
            'bold': True, 'font_size': 18, 'align': 'center'
        })
        table_head = workbook.add_format({
            'bold': True, 'align': 'center', 'border': 1
        })
        text = workbook.add_format({
            'align': 'center', 'border': 1
        })

        # Column widths
        sheet.set_column('B:B', 18)
        sheet.set_column('C:C', 18)
        sheet.set_column('D:D', 20)
        sheet.set_column('E:E', 20)
        sheet.set_column('F:F', 22)
        sheet.set_column('G:G', 22)

        # Table headers
        row = 1
        col = 0
        headers = [
            'Sl No',
            'Vehicle No',
            'Total Capacity',
            'Assigned Students',
            'Available Seats',
            'Occupancy (%)'
        ]

        for idx, header in enumerate(headers):
            sheet.write(row, col + idx, header, table_head)

        # SQL (same as PDF)
        params = []
        query = """
              SELECT
                    v.reg_no AS vehicle_no,v.capacity AS total_capacity,
                    COUNT(a.id) AS assigned_students,
                    (v.capacity - COUNT(a.id)) AS available_seats,
                    ROUND(
                        ((COUNT(a.id)::numeric / NULLIF(v.capacity, 0)) * 100),
                        2
                    ) AS occupancy_percentage
                FROM fleet_vehicle v
                LEFT JOIN education_transport_route r
                    ON r.vehicle_id = v.id AND r.active = TRUE
                LEFT JOIN education_transport_assignment a
                    ON a.route_id = r.id AND a.active = TRUE
                WHERE v.is_transport_vehicle = TRUE
            """

        if data.get('vehicle_ids'):
            query += " AND v.id IN %s"
            params.append(tuple(data['vehicle_ids']))

        query += " GROUP BY v.id, v.reg_no, v.capacity"

        if data.get('report_type') == 'over':
            query += " HAVING COUNT(a.id) >= v.capacity"

        if data.get('report_type') == 'available':
            query += " HAVING COUNT(a.id) < v.capacity"

        self.env.cr.execute(query, params)
        records = self.env.cr.fetchall()

        # Write data
        row += 1
        sl_no = 1
        for rec in records:
            sheet.write(row, col, sl_no, text)
            for i, value in enumerate(rec):
                sheet.write(row, col + i + 1, value, text)
            row += 1
            sl_no += 1

        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()

