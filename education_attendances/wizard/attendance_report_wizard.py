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
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet("Attendance Report")

        header = workbook.add_format({'bold': True, 'border': 1, 'align': 'center'})
        cell = workbook.add_format({'border': 1})

        headers = ["Student", "Class", "Program", "Date", "Status", "Remarks"]
        for col, h in enumerate(headers):
            sheet.write(0, col, h, header)

        # ---------------- SQL QUERY ----------------
        query = """
                SELECT
                    rp.name AS student_name,
                    ec.name AS class_name,
                    ep.name AS program_name,
                    ea.date,
                    ea.state AS status,
                    ea.remarks
                FROM education_attendance ea
                JOIN res_partner rp ON rp.id = ea.student_id
                LEFT JOIN education_class ec ON ec.id = ea.class_id
                LEFT JOIN education_program ep ON ep.id = ea.program_id
                WHERE ea.state IS NOT NULL
            """

        params = []

        # Student filter (single / multiple)
        if data.get('student_ids'):
            query += " AND ea.student_id = ANY(%s)"
            params.append(data['student_ids'])

        # Class filter
        if data.get('choice') == 'class' and data.get('class_id'):
            query += " AND ea.class_id = %s"
            params.append(data['class_id'])

        # Program filter
        if data.get('choice') == 'program' and data.get('program_id'):
            query += " AND ea.program_id = %s"
            params.append(data['program_id'])

        # Date filters
        if data.get('based_on') == 'custom' and data.get('date_from') and data.get('date_to'):
            query += " AND ea.date BETWEEN %s AND %s"
            params.extend([data['date_from'], data['date_to']])

        elif data.get('based_on') == 'monthly':
            query += " AND date_trunc('month', ea.date) = date_trunc('month', CURRENT_DATE)"

        elif data.get('based_on') == 'yearly':
            query += " AND date_part('year', ea.date) = date_part('year', CURRENT_DATE)"

        query += " ORDER BY ea.date, rp.name"

        self.env.cr.execute(query, params)
        records = self.env.cr.fetchall()

        # ---------------- WRITE XLSX ----------------
        row = 1
        for rec in records:
            for col, value in enumerate(rec):
                sheet.write(row, col, value or '', cell)
            row += 1

        workbook.close()
        output.seek(0)
        response.stream.write(output)