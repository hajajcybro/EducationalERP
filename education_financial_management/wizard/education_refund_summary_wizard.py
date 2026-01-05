# -*- coding: utf-8 -*-
from odoo import models, fields
import io
import json
import xlsxwriter
from odoo.tools import json_default

class RefundSummaryWizard(models.TransientModel):
    _name = 'refund.summary.wizard'
    _description = 'Refund Summary Wizard'

    student_ids = fields.Many2many(
        'res.partner',
        string='Students',
        domain=[('is_student', '=', True)]
    )
    refund_state = fields.Selection(
        [
            ('all', 'All'),
            ('draft', 'Draft'),
            ('approved', 'Approved'),
            ('processed', 'Processed'),
            ('rejected', 'Rejected'),
        ],
        default='all',
        string='Refund Status'
    )

    date_filter = fields.Selection(
        [('daily', 'Today'), ('weekly', 'This Week'),
            ('monthly', 'This Month'),('custom', 'Custom'),
        ],
        string='Date Filter'
    )
    from_date = fields.Date()
    to_date = fields.Date()

    def action_generate_refund_pdf_report(self):
        data = {
            'student_ids': self.student_ids.ids,
            'refund_state': self.refund_state,
            'date_filter': self.date_filter,
            'from_date': self.from_date,
            'to_date': self.to_date,
        }
        return self.env.ref(
            'education_financial_management.action_refund_summary_report'
        ).report_action(None, data=data)

    def action_generate_refund_xlsx_report(self):
        """Button action for generate xlxs report"""

        data = {
            'model_id': 'refund.summary.wizard',
            'student_ids': self.student_ids.ids,
            'refund_state': self.refund_state,
            'date_filter': self.date_filter,
            'from_date': self.from_date,
            'to_date': self.to_date,
        }
        return {
            'type': 'ir.actions.report',
            'data': {'model': 'refund.summary.wizard',
                     'options': json.dumps(data, default=json_default),
                     'output_format': 'xlsx',
                     'report_name': 'Refund Excel Report',
                     },
            'report_type': 'xlsx',
        }

    def get_xlsx_report(self, data, response):
        """Action for create XLXS report for student leave details"""
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet('Refund Summary')

        header = workbook.add_format({'bold': True, 'border': 1, 'align': 'center'})
        text = workbook.add_format({'border': 1, 'align': 'center'})
        date_fmt = workbook.add_format({
            'border': 1, 'align': 'center', 'num_format': 'yyyy-mm-dd'
        })
        amount_fmt = workbook.add_format({
            'border': 1, 'align': 'right', 'num_format': '#,##0.00'
        })

        sheet.set_column('A:A', 6)
        sheet.set_column('B:B', 20)
        sheet.set_column('C:C', 18)
        sheet.set_column('D:D', 18)
        sheet.set_column('E:E', 14)
        sheet.set_column('F:F', 16)
        sheet.set_column('G:G', 18)
        sheet.set_column('H:H', 18)
        sheet.set_column('I:I', 22)
        sheet.set_column('J:J', 22)

        headers = [
            'Sl No', 'Student', 'Admission No', 'Invoice',
            'Request Date', 'Refund Status',
            'Requested Amount', 'Credit Note Amount',
            'Reason', 'Rejection Reason'
        ]

        for col, h in enumerate(headers):
            sheet.write(0, col, h, header)

        query = """SELECT rr.id AS refund_id,
                         rp.name AS student_name,
                         rp.admission_no,
                         am.name AS invoice_number,
                         rr.create_date::date AS request_date,
                         rr.state AS refund_state,
                         rr.refund_amount AS requested_refund_amount,
                         rr.reason,
                         rr.rejection_reason,
                         cn.name AS credit_note,
                         cn.amount_total AS credit_note_amount
                     FROM education_refund_request rr
                              JOIN res_partner rp ON rp.id = rr.student_id
                              LEFT JOIN account_move am ON am.id = rr.invoice_id
                              LEFT JOIN account_move cn
                                        ON cn.reversed_entry_id = am.id
                                            AND cn.move_type = 'out_refund'
                                            AND cn.state = 'posted'
                     WHERE rp.is_student = TRUE"""

        if data.get('student_ids'):
            student_ids = tuple(data['student_ids'])
            if len(student_ids) == 1:
                query += " AND rp.id = %s" % student_ids[0]
            else:
                query += " AND rp.id IN %s" % (student_ids,)

        if data.get('refund_state') and data['refund_state'] != 'all':
            query += " AND rr.state = '%s'" % data['refund_state']

        if data.get('date_filter') == 'daily':
            query += " AND rr.create_date::date = CURRENT_DATE"

        elif data.get('date_filter') == 'weekly':
            query += """
                                         AND DATE_TRUNC('week', rr.create_date)
                                             = DATE_TRUNC('week', CURRENT_DATE) """

        elif data.get('date_filter') == 'monthly':
            query += """
                                         AND DATE_TRUNC('month', rr.create_date)
                                             = DATE_TRUNC('month', CURRENT_DATE) """

        elif data.get('date_filter') == 'custom':
            if data.get('from_date'):
                query += " AND rr.create_date::date >= '%s'" % data['from_date']
            if data.get('to_date'):
                query += " AND rr.create_date::date <= '%s'" % data['to_date']

        self.env.cr.execute(query)
        rows = self.env.cr.fetchall()

        row_no = 1
        for idx, r in enumerate(rows, start=1):
            sheet.write(row_no, 0, idx, text)  # Sl No
            sheet.write(row_no, 1, r[1] or '-', text)  # Student
            sheet.write(row_no, 2, r[2] or '-', text)  # Admission No
            sheet.write(row_no, 3, r[3] or '-', text)  # Invoice
            sheet.write(row_no, 4, r[4] or '-', date_fmt)  # Request Date
            sheet.write(row_no, 5, r[5] or '-', text)  # Refund Status
            sheet.write(row_no, 6, r[6] or 0.0, amount_fmt)  # Requested Amount
            sheet.write(row_no, 7, r[10] or 0.0, amount_fmt)  # Credit Note Amount
            sheet.write(row_no, 8, r[7] or '-', text)  # Reason
            sheet.write(row_no, 9, r[8] or '-', text)  # Rejection Reason
            row_no += 1

        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()






