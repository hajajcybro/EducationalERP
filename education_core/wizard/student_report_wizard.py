# -*- coding: utf-8 -*-
from odoo import models, fields
import io
import json
import xlsxwriter
from odoo.tools import json_default
from redis.cluster import PRIMARY


class StudentReportWizard(models.TransientModel):
    """create model for manage leaves"""
    _name = 'student.report.wizard'
    _description = 'Student Wizard report'

    choice = fields.Selection([
        ('class', 'Class'),
        ('student', 'Student'),
        ('program', 'Program'),
        ('academic_year', 'Academic Year'),
    ], string="Filter By", required=True)

    academic_year_id = fields.Many2one('education.academic.year', string="Academic Year")
    class_id = fields.Many2one('education.class', string="Class")
    student_ids = fields.Many2many(
        'res.partner',
        string='Students',
        domain=[('is_student', '=', True)]
    )
    program_id = fields.Many2one('education.program', string="Program")

    def action_generate_pdf(self):
        print('pdf')
        """Create button action for pdf report"""
        # print(self.read())
        data = {
            'choice': self.choice,
            'academic_year_id': self.academic_year_id.id,
            'class_id': self.class_id.id,
            'student_ids': self.student_ids.ids,
            'program_id' : self.program_id.id,
        }
        print(data)
        return self.env.ref('education_core.action_report_student_information').report_action(None, data=data)



    def action_generate_xl_report(self):
        """Button action for generate xlxs report"""
        print('XLSX')
        data = {
            'model_id': 'student.report.wizard',
            'choice': self.choice,
            'academic_year_id': self.academic_year_id.id,
            'class_id': self.class_id.id,
            'student_ids': self.student_ids.ids,
            'program_id' : self.program_id.id,

        }
        print("xlllll")
        return {
            'type': 'ir.actions.report',
            'data': {'model': 'student.report.wizard',
                     'options': json.dumps(data, default=json_default),
                     'output_format': 'xlsx',
                     'report_name': 'Student Report',
                     },
            'report_type': 'xlsx',
        }

    def get_xlsx_report(self, data, response):
        print("Generating XLSX")

        # Fetch SQL result (reuse your report model)
        report_model = self.env['report.education_core.report_student_details']
        values = report_model._get_report_values([], data=data)
        records = values.get('docs', [])

        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet("Student Report")

        # ======= STYLES =======
        header_format = workbook.add_format({
            'bold': True,
            'font_size': 12,
            'align': 'center',
            'valign': 'vcenter',
            'bg_color': '#D9D9D9',
            'border': 1
        })

        cell_format = workbook.add_format({
            'align': 'center',
            'valign': 'vcenter',
            'border': 1
        })

        # Auto column sizes
        column_widths = [16, 15, 10, 25, 15, 17, 26]

        for col, width in enumerate(column_widths):
            sheet.set_column(col, col, width)

        # Freeze header row
        sheet.freeze_panes(1, 0)
        headers = [
            "Admission No", "Name", "Roll No", "Email",
            "Phone", "Class", "Program", "Academic Year"
        ]

        for col, header in enumerate(headers):
            sheet.write(0, col, header, header_format)
        row = 1
        for rec in records:
            sheet.write(row, 0, rec.get('admission_no', ''), cell_format)
            sheet.write(row, 1, rec.get('student_name', ''), cell_format)
            sheet.write(row, 2, rec.get('roll_no', ''), cell_format)
            sheet.write(row, 3, rec.get('email', ''), cell_format)
            sheet.write(row, 4, rec.get('phone', ''), cell_format)
            sheet.write(row, 5, rec.get('class_name', ''), cell_format)
            sheet.write(row, 6, rec.get('program_name', ''), cell_format)
            sheet.write(row, 7, rec.get('academic_year', ''), cell_format)
            row += 1

        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()

