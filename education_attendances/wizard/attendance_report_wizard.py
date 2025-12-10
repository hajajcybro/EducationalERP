# -*- coding: utf-8 -*-
from odoo import models, fields
from datetime import date
import io
import json
import xlsxwriter
from odoo.tools import json_default

class AttendanceReportWizard(models.TransientModel):
    _name = 'attendance.report.wizard'
    _description = 'Attendance Report Wizard'

    choice = fields.Selection([
        ('student', 'Student'),
        ('class', 'Class'),
        ('program', 'Program'),
    ], string="Filter By", required=True)

    student_ids = fields.Many2many(
        'res.partner',
        domain=[('is_student', '=', True)],
        string="Students"
    )
    class_id = fields.Many2one('education.class', string="Class")
    program_id = fields.Many2one('education.program', string="Program")

    based_on = fields.Selection([
        ('monthly', 'Monthly'),
        ('yearly', 'Yearly'),
        ('custom', 'Custom Range'),
    ], string="Date Filter")

    date_from = fields.Date(string="From Date")
    date_to = fields.Date(string="To Date")

    def action_generate_pdf(self):
        print('pdf')
        data = {
            'choice': self.choice,
            'student_ids': self.student_ids.ids,
            'class_id': self.class_id.id,
            'program_id': self.program_id.id,
            'based_on': self.based_on,
            'date_from': self.date_from,
            'date_to': self.date_to,
        }
        return self.env.ref('education_attendances.action_report_student_attendance').report_action(self, data=data)

    def action_generate_xl_report(self):
        data = {
            'model_id': 'attendance.report.wizard',
            'choice': self.choice,
            'student_ids': self.student_ids.ids,
            'class_id': self.class_id.id,
            'program_id': self.program_id.id,
            'based_on': self.based_on,
            'date_from': self.date_from,
            'date_to': self.date_to,
        }

        return {
            'type': 'ir.actions.report',
            'data': {
                'model': 'attendance.report.wizard',
                'options': json.dumps(data, default=json_default),
                'output_format': 'xlsx',
                'report_name': 'Attendance Report',
            },
            'report_type': 'xlsx',
        }

    def get_xlsx_report(self, data, response):
        _query_model = self.env['report.education_attendances.student_report_attendance']
        report_data = _query_model._get_report_values([], data)['docs']

        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})

        sheet = workbook.add_worksheet("Attendance Report")

        header_format = workbook.add_format({'bold': True, 'bg_color': '#D9D9D9', 'border': 1, 'align': 'center'})
        cell_format = workbook.add_format({'border': 1})

        headers = ["Student", "Class", "Program", "Date", "Status", "Remarks"]

        for col, head in enumerate(headers):
            sheet.write(0, col, head, header_format)

        for row, line in enumerate(report_data, 1):
            sheet.write(row, 0, line.get('student_name'), cell_format)
            sheet.write(row, 1, line.get('class_name'), cell_format)
            sheet.write(row, 2, line.get('program_name'), cell_format)
            sheet.write(row, 3, line.get('date'), cell_format)
            sheet.write(row, 4, line.get('status'), cell_format)
            sheet.write(row, 5, line.get('remarks'), cell_format)

        workbook.close()
        response.stream.write(output.getvalue())
        output.close()