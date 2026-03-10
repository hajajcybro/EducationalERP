# -*- coding: utf-8 -*-
import json
from odoo import http
from odoo.http import content_disposition, request
from odoo.tools import html_escape


class LibraryXLSXReportController(http.Controller):
    @http.route('/library_xlsx_reports', type='http', auth='user', csrf=False)
    def get_library_xlsx_report(self, model, options, output_format, report_name, token='token'):
        """Return XLSX report data"""
        session_unique_id = request.session.uid
        report_object = request.env[model].with_user(session_unique_id)
        options = json.loads(options)

        try:
            if output_format == 'xlsx':
                response = request.make_response(
                    None,
                    headers=[
                        ('Content-Type', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'),
                        ('Content-Disposition', content_disposition(f"{report_name}.xlsx"))
                    ]
                )
                report_object.get_xlsx_report(options, response)
                response.set_cookie('fileToken', token)
                return response
        except Exception as e:
            error = {
                'code': 200,
                'message': f'Error generating XLSX report: {str(e)}',
            }
            return request.make_response(html_escape(json.dumps(error)))