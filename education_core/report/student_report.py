# -*- coding: UTF-8 -*-
from odoo import models, api
from datetime import date, timedelta

class StudentReport(models.AbstractModel):
    _name = 'report.education_core.report_student_details'

    @api.model
    def _get_report_values(self, docids, data=None):
        print("Abstract")
        query  = """SELECT rp.admission_no, rp.name AS student_name, rp.roll_no, rp.email,rp.phone, ec.name AS class_name,ep.name AS program_name,eay.name AS academic_year 
                    FROM res_partner rp 
                    LEFT JOIN education_class ec ON rp.class_id = ec.id
                    LEFT JOIN education_program ep ON rp.program_id = ep.id
                    LEFT JOIN education_academic_year eay  ON rp.academic_year_id = eay.id
                    WHERE 
                    rp.is_student = TRUE
                    AND rp.active = TRUE
                     """
        if data:
            choice = data.get('choice')
            based_on = data.get('based_on')

            if choice == 'class':
                query += " AND rp.class_id = %s" % data.get('class_id')
                print(query)

            if choice == 'student':
                student_ids = data.get('student_ids') or []
                if student_ids:
                    query += " AND rp.id IN %s" % (tuple(student_ids),)
                    print(query)

            if choice == 'program':
                program_id = data.get('program_id')
                if program_id:
                    query += " AND rp.program_id = %s" % program_id
                    print(query)

            if choice == 'academic_year':
                academic_year_id = data.get('academic_year_id')
                if academic_year_id:
                    query += " AND rp.academic_year_id = %s" % academic_year_id
                    print(query)

        # ORDER BY
        print("SQL Used:", query)
        # Execute SQL
        self.env.cr.execute(query)
        records = self.env.cr.dictfetchall()
        return {
            'doc_ids': docids,
            'doc_model': 'res.partner',
            'docs': records,
            'data':data,
        }
