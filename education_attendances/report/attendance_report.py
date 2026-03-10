# -*- coding: utf-8 -*-
from odoo import models, api
from datetime import date, timedelta

class AttendanceReport(models.AbstractModel):
    _name = 'report.education_attendances.student_report_attendance'

    @api.model
    def _get_report_values(self, docids, data=None):
        query = """
            SELECT
                rp.name AS student_name,
                att.date AS date,
                cl.name AS class_name,
                pr.name AS program_name,
                line.status AS status,
                line.remarks AS remarks
            FROM education_attendance_line line
            LEFT JOIN education_attendance att ON line.attendance_id = att.id
            LEFT JOIN res_partner rp ON line.student_id = rp.id
            LEFT JOIN education_class cl ON att.class_id = cl.id
            LEFT JOIN education_program pr ON att.program_id = pr.id
            WHERE att.state = 'validated'
        """
        print(query)

        if data:

            choice = data.get('choice')
            based_on = data.get('based_on')

            # FILTER BY STUDENT / CLASS / PROGRAM
            if choice == 'student' and data.get('student_ids'):
                ids = tuple(data['student_ids'])
                if len(ids) == 1:
                    query += " AND line.student_id = %s" % ids[0]
                else:
                    query += " AND line.student_id IN %s" % (ids,)

            if choice == 'class' and data.get('class_id'):
                query += " AND att.class_id = %s" % data['class_id']

            if choice == 'program' and data.get('program_id'):
                query += " AND att.program_id = %s" % data['program_id']

            today = date.today()

            if based_on == 'monthly':
                start = today.replace(day=1)
                if today.month == 12:
                    end = date(today.year, 12, 31)
                else:
                    end = (today.replace(month=today.month + 1, day=1) - timedelta(days=1))
                query += " AND att.date BETWEEN '%s' AND '%s'" % (start, end)

            # YEARLY
            elif based_on == 'yearly':
                start = date(today.year, 1, 1)
                end = date(today.year, 12, 31)
                query += " AND att.date BETWEEN '%s' AND '%s'" % (start, end)

            # CUSTOM
            elif based_on == 'custom' and data.get('date_from') and data.get('date_to'):
                query += " AND att.date BETWEEN '%s' AND '%s'" % (
                    data['date_from'], data['date_to']
                )

        self.env.cr.execute(query)
        records = self.env.cr.dictfetchall()

        return {
            'docs': records,
            'data': data,
        }
