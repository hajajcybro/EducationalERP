# -*- coding: utf-8 -*-
from odoo import models, fields
import io
import json
import xlsxwriter
from odoo.tools import json_default


class InvoiceSummaryWizard(models.TransientModel):
    _name = 'invoice.summary.wizard'
    _description = 'Invoice Summary Wizard'

    student_ids = fields.Many2many(
        'res.partner',
        string='Students',
        domain=[('is_student', '=', True)]
    )

    date_filter = fields.Selection(
        [
            ('daily', 'Today'),
            ('weekly', 'This Week'),
            ('monthly', 'This Month'),
            ('custom', 'Custom'),
        ],
        string='Date Filter'
    )

    from_date = fields.Date()
    to_date = fields.Date()

    invoice_type = fields.Selection(
        [
            ('all', 'All'),
            ('out_invoice', 'Customer Invoice'),
            ('out_refund', 'Customer Credit Note'),
        ],
        default='all',
        string='Invoice Type'
    )

    payment_state = fields.Selection(
        [
            ('all', 'All'),
            ('not_paid', 'Not Paid'),
            ('partial', 'Partially Paid'),
            ('paid', 'Paid'),
        ],
        default='all',
        string='Payment Status'
    )

    def action_generate_pdf_report(self):
        data = {
            'student_ids': self.student_ids.ids,
            'date_filter': self.date_filter,
            'from_date': self.from_date,
            'to_date': self.to_date,
            'invoice_type': self.invoice_type,
            'payment_state': self.payment_state,
        }

        return self.env.ref(
            'education_financial_management.action_invoice_summary_report'
        ).report_action(None, data=data)

    def action_generate_invoice_xlsx_report(self):
        """Button action for generate xlxs report"""
        data = {
            'model_id': 'invoice.summary.wizard',
            'student_ids': self.student_ids.ids,
            'date_filter': self.date_filter,
            'from_date': self.from_date,
            'to_date': self.to_date,
            'invoice_type': self.invoice_type,
            'payment_state': self.payment_state,

        }
        return {
            'type': 'ir.actions.report',
            'data': {'model': 'invoice.summary.wizard',
                     'options': json.dumps(data, default=json_default),
                     'output_format': 'xlsx',
                     'report_name': 'Invoice Excel Report',
                     },
            'report_type': 'xlsx',
        }

    def get_xlsx_report(self, data, response):
        """Action for create XLXS report for student leave details"""
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet('Invoice Summary')
        header = workbook.add_format({
            'bold': True, 'border': 1, 'align': 'center'
        })
        text = workbook.add_format({
            'border': 1, 'align': 'center'
        })
        date_fmt = workbook.add_format({
            'border': 1, 'align': 'center', 'num_format': 'yyyy-mm-dd'
        })
        amount_fmt = workbook.add_format({
            'border': 1, 'align': 'right', 'num_format': '#,##0.00'
        })

        sheet.set_column('A:A', 6)  # Sl No
        sheet.set_column('B:B', 18)  # Student
        sheet.set_column('C:C', 18)  # Admission No
        sheet.set_column('D:D', 22)  # Invoice No
        sheet.set_column('E:E', 22)  # Invoice Type
        sheet.set_column('F:F', 14)  # Invoice Date
        sheet.set_column('G:G', 14)  # Due Date
        sheet.set_column('H:H', 14)  # Total
        sheet.set_column('I:I', 14)  # Residual
        sheet.set_column('J:J', 16)  # Payment State
        headers = [
                'Sl No', 'Student', 'Admission No', 'Invoice No',
                'Invoice Type', 'Invoice Date', 'Due Date',
                'Total', 'Residual', 'Payment Status'
        ]

        for col, h in enumerate(headers):
            sheet.write(0, col, h, header)
        params = []
        query = """SELECT rp.name AS student_name, 
                           rp.admission_no, 
                           am.name AS invoice_number, 
                           am.move_type ,
                           am.invoice_date, 
                           am.invoice_date_due, 
                           am.amount_total, 
                           am.amount_residual, 

	                           CASE am.payment_state 
                               WHEN 'not_paid' THEN 'Not Paid' 
                               WHEN 'partial' THEN 'Partially Paid' 
                               WHEN 'paid' THEN 'Paid' 
                               WHEN 'reversed' THEN 'Reversed' 
                               WHEN 'in_payment' THEN 'In Payment' 
                               ELSE am.payment_state 
                               END AS payment_state

                    FROM account_move am
                             JOIN res_partner rp ON rp.id = am.partner_id
                    WHERE am.state = 'posted'
                      AND rp.is_student = TRUE """

        if data.get('student_ids'):
            if len(data['student_ids']) == 1:
                query += " AND rp.id = %s"
                params.append(data['student_ids'][0])
            else:
                query += " AND rp.id IN %s"
                params.append(tuple(data['student_ids']))

        if data.get('invoice_type') and data['invoice_type'] != 'all':
            query += " AND am.move_type = '%s'" % data['invoice_type']
        if data.get('payment_state') and data['payment_state'] != 'all':
            query += " AND am.payment_state = '%s'" % data['payment_state']

        if data.get('date_filter') == 'daily':
            query += " AND am.invoice_date = CURRENT_DATE"

        elif data.get('date_filter') == 'weekly':
            query += """
                AND DATE_TRUNC('week', am.invoice_date)
                    = DATE_TRUNC('week', CURRENT_DATE)
            """

        elif data.get('date_filter') == 'monthly':
            query += """
                AND DATE_TRUNC('month', am.invoice_date)
                    = DATE_TRUNC('month', CURRENT_DATE)
            """

        elif data.get('date_filter') == 'custom':
            if data.get('from_date'):
                    query += " AND am.invoice_date >= '%s'" % data['from_date']
            if data.get('to_date'):
                    query += " AND am.invoice_date <= '%s'" % data['to_date']

        self.env.cr.execute(query,params)
        rows = self.env.cr.fetchall()

        row_no = 1
        for idx, r in enumerate(rows, start=1):
            sheet.write(row_no, 0, idx, text)
            sheet.write(row_no, 1, r[0] or '-', text)
            sheet.write(row_no, 2, r[1] or '-', text)
            sheet.write(row_no, 3, r[2] or '-', text)
            sheet.write(row_no, 4, r[3] or '-', text)
            sheet.write(row_no, 5, r[4] or '-', date_fmt)
            sheet.write(row_no, 6, r[5] or '-', date_fmt)
            sheet.write(row_no, 7, r[6] or 0.0, amount_fmt)
            sheet.write(row_no, 8, r[7] or 0.0, amount_fmt)
            sheet.write(row_no, 9, r[8] or '-', text)
            row_no += 1
        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()
