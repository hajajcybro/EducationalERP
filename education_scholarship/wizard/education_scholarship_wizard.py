from odoo import models, fields
import io
import json
import xlsxwriter
from odoo.tools import json_default

class ScholarshipWizard(models.TransientModel):
    _name = 'scholarship.wizard'
    _description = 'Scholarship Wizard'

    academic_year_id = fields.Many2one(
        'education.academic.year',
        string='Academic Year'
    )
    session_id = fields.Many2one(
        'education.session',
        string='Semester / Session'
    )
    program_id = fields.Many2one(
        'education.program',
        string='Program'
    )
    scholarship_id = fields.Many2one(
        'education.scholarship',
        string='Scholarship'
    )
    application_state = fields.Selection([
        ('submitted', 'Submitted'),
        ('under_review', 'Under Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ], string='Application Status', default='approved')
    date_from = fields.Date(string='Application Date From')
    date_to = fields.Date(string='Application Date To')
    student_ids = fields.Many2many(
        'res.partner',
        string='Student',
        domain=[('position_role', '=', 'student')]
    )
    has_remaining_amount = fields.Selection([
        ('yes', 'Has Remaining Amount'),
        ('no', 'No Remaining Amount'),
    ], string='Remaining Scholarship')

    def action_generate_scholarship_report(self):
        """Create button action for pdf report"""
        data = {
            'academic_year_id': self.academic_year_id.id,
            'session_id': self.session_id.id,
            'program_id': self.program_id.id,
            'scholarship_id': self.scholarship_id.id,
            'application_state': self.application_state,
            'date_from': self.date_from,
            'date_to': self.date_to,
            'student_ids': self.student_ids.ids,
            'has_remaining_amount': self.has_remaining_amount,
        }
        return self.env.ref('education_scholarship.action_report_scholarship_information').report_action(None, data=data)

    def action_generate_scholarship_XLSX_report(self):
        """Button action for generate xlxs report"""
        data = {
             'model_id': 'scholarship.wizard',
            'academic_year_id': self.academic_year_id.id if self.academic_year_id else False,
            'session_id': self.session_id.id if self.session_id else False,
            'program_id': self.program_id.id if self.program_id else False,
            'scholarship_id': self.scholarship_id.id if self.scholarship_id else False,
            'application_state': self.application_state,
            'date_from': self.date_from,
            'date_to': self.date_to,
            'student_ids': self.student_ids.ids if self.student_ids else [],
            'has_remaining_amount': self.has_remaining_amount,
        }
        return {
            'type': 'ir.actions.report',
            'data': {'model': 'scholarship.wizard',
                     'options': json.dumps(data, default=json_default),
                     'output_format': 'xlsx',
                     'report_name': 'Scholarship Report',
                     },
            'report_type': 'xlsx',
        }

    def get_xlsx_report(self, data, response):
        """Generate Scholarship XLSX Report"""

        import io
        import xlsxwriter
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet('Scholarship Report')
        head = workbook.add_format({'align': 'center', 'bold': True, 'font_size': 18})
        table_head = workbook.add_format({'align': 'center', 'bold': True, 'font_size': 11})
        text = workbook.add_format({'align': 'center','font_size': 10})
        sheet.merge_range('B2:J3', 'SCHOLARSHIP REPORT', head)
        sheet.set_column('B:B', 22)
        sheet.set_column('C:C', 18)
        sheet.set_column('D:D', 18)
        sheet.set_column('E:E', 16)
        sheet.set_column('F:F', 22)
        sheet.set_column('G:G', 16)
        sheet.set_column('H:H', 18)
        sheet.set_column('I:I', 16)
        sheet.set_column('J:J', 18)

        row = 4
        col = 0
        headers = [
            "Student", "Academic Year", "Program", "Session",
            "Scholarship", "Duration", "Status",
            "Application Date", "Amount", "Remaining"
        ]
        for header in headers:
            sheet.write(row, col, header, table_head)
            col += 1
        query = """SELECT
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
            session_id = data['session_id']
            if isinstance(session_id, list):
                session_id = session_id[0]
            query += " AND ses.id = %s" % int(session_id)
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
        records = self.env.cr.fetchall()
        row = 5
        num = 1
        for rec in records:
            col = 0
            for value in rec:
                sheet.write(row, col, value or '', text)
                col += 1
            row += 1
            num += 1
        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()
