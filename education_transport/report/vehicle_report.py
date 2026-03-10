# -*- coding: UTF-8 -*-
from odoo import models, api

class VehicleReport(models.AbstractModel):
    _name = 'report.education_transport.report_vehicle_details'

    @api.model
    def _get_report_values(self, docids, data=None):
        data = data or {}

        vehicle_ids = data.get('vehicle_ids') or []
        report_type = data.get('report_type')

        params = []
        query = """
                SELECT
                    v.reg_no AS vehicle_no,
                    v.capacity AS total_capacity,
                    COUNT(a.id) AS assigned_students,
                    (v.capacity - COUNT(a.id)) AS available_seats,
                    ROUND(
                        ((COUNT(a.id)::numeric / NULLIF(v.capacity, 0)) * 100),
                        2
                    ) AS occupancy_percentage
                FROM fleet_vehicle v
                LEFT JOIN education_transport_route r
                    ON r.vehicle_id = v.id
                    AND r.active = TRUE
                LEFT JOIN education_transport_assignment a
                    ON a.route_id = r.id
                    AND a.active = TRUE
                WHERE v.is_transport_vehicle = TRUE
            """

        #specific vehicles selected (Many2many)
        if vehicle_ids:
            query += " AND v.id IN %s"
            params.append(tuple(vehicle_ids))

        query += " GROUP BY v.id, v.reg_no, v.capacity"

        if report_type == 'over':
            query += " HAVING COUNT(a.id) >= v.capacity"

        if report_type == 'available':
            query += " HAVING COUNT(a.id) < v.capacity"

        self.env.cr.execute(query, params)
        records = self.env.cr.dictfetchall()
        print(records)

        return {
            'docs': records,
            'data': data,
        }

