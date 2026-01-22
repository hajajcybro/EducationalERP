# -*- coding: UTF-8 -*-
from odoo import models, api

class ScholarshipReport(models.AbstractModel):
    _name = 'report.education_scholarship.scholarship_report_template'

    @api.model
    def _get_report_values(self, docids, data=None):
        query="""SELECT
            rp.name AS student, ay.name AS academic_year,
            prog.name AS program, ses.name AS session,
            sch.name AS scholarship, sch.application_duration,
            app.state AS application_status, app.application_date AS application_date,
            sch.scholarship_amount,  app.scholarship_remaining_amount
        FROM education_scholarship_application app
        JOIN res_partner rp ON rp.id = app.student_id
        LEFT JOIN education_scholarship sch ON sch.id = app.scholarship_id
        LEFT JOIN education_academic_year ay ON ay.id = sch.academic_year_id
        LEFT JOIN education_program prog ON prog.id = rp.program_id
        LEFT JOIN education_class cls ON cls.id = rp.class_id
        LEFT JOIN education_session ses ON ses.id = cls.session_id
        WHERE 1=1"""

        if data.get('academic_year_id'):
            print('academic_year')
            query += " AND ay.id = %s" % data['academic_year_id']

        if data.get('program_id'):
            query += " AND prog.id = %s" % data['program_id']

        if data.get('session_id'):
            query += " AND ses.id = %s" % data['session_id']

        if data.get('scholarship_id'):
            query += " AND sch.id = %s" % data['scholarship_id']

        if data.get('application_state'):
            query += " AND app.state = '%s'" % data['application_state']

        if data.get('student_ids'):
            student_ids = data['student_ids']
            ids_str = ','.join(map(str, student_ids))
            query += f" AND rp.id IN ({ids_str})"

        if data.get('date_from') and data.get('date_to'):
            query += " AND app.application_date BETWEEN '%s' AND '%s'" % (
                data['date_from'], data['date_to']
            )

        elif data.get('date_from'):
            query += " AND app.application_date >= '%s'" % data['date_from']

        elif data.get('date_to'):
            query += " AND app.application_date <= '%s'" % data['date_to']

        if data.get('has_remaining_amount') == 'yes':
            query += " AND app.scholarship_remaining_amount > 0"

        elif data.get('has_remaining_amount') == 'no':
            query += " AND app.scholarship_remaining_amount <= 0"
        self.env.cr.execute(query)
        report = self.env.cr.fetchall()
        return {
                    'doc_ids': docids,
                    'doc_model': 'scholarship.wizard',
                    'docs': report,
                    'data': data,
                }

