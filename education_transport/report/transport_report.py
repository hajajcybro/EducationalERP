# -*- coding: UTF-8 -*-
from odoo import models, api

class TransportReport(models.AbstractModel):
    _name = 'report.education_transport.report_transport_details'

    @api.model
    def _get_report_values(self, docids, data=None):
        print('report value')

        data = data or {}
        params = []

        query = """SELECT rp.name AS student_name,
                r.name AS route_name, s.stop_name,
                s.pickup_time, s.drop_time
            FROM education_transport_assignment a
            JOIN res_partner rp ON rp.id = a.student_id
            JOIN education_transport_route r ON r.id = a.route_id
            JOIN education_transport_stop s ON s.id = a.stop_id
            WHERE a.active = TRUE"""

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

        return {
            'doc_ids': docids,
            'doc_model': 'education.transport.assignment',
            'docs': records,
            'data': data,
        }
