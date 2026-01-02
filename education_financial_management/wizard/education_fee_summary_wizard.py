# -*- coding: utf-8 -*-
from odoo import models, fields
from datetime import date
import io
import json
import xlsxwriter
from odoo.tools import json_default


class FeeSummaryWizard(models.TransientModel):
    _name = 'fee.summary.wizard'
    _description = 'Fee Summary Wizard'

    student_ids = fields.Many2many(
        'res.partner',
        string='Students',
        domain=[('is_student', '=', True)]
    )
    date_filter = fields.Selection(
        [('daily', 'Daily'), ('weekly', 'Weekly'),('monthly', 'Monthly'),('custom', 'Custom'),],
        string='Date Filter',
    )
    from_date = fields.Date(string='From Date')
    to_date = fields.Date(string='To Date')

    payment_type = fields.Selection(
        [('all', 'All'),('full', 'Full Payment'),
            ('installment', 'Installment'),],
        string='Payment Type',
        default='all'
    )
    is_refund = fields.Boolean(
        string='Refund',
    )

    def action_generate_pdf_report(self):
        """Create button action for pdf report"""
        data = {
            'student_ids': self.student_ids.ids,
            'date_filter': self.date_filter,
            'from_date': self.from_date,
            'to_date': self.to_date,
            'payment_type': self.payment_type,
            'is_refund': self.is_refund,
        }
        print(data)
        return self.env.ref('education_financial_management.action_report_fee_summary').report_action(None, data=data)


    def action_generate_xlsx_report(self):
        """Button action for generate xlxs report"""
        data = {
            'model_id': 'fee.summary.wizard',
            'student_ids': self.student_ids.ids,
            'date_filter': self.date_filter,
            'from_date': self.from_date,
            'to_date': self.to_date,
            'payment_type': self.payment_type,
            'is_refund': self.is_refund,
        }
        return {
            'type': 'ir.actions.report',
            'data': {'model': 'fee.summary.wizard',
                     'options': json.dumps(data, default=json_default),
                     'output_format': 'xlsx',
                     'report_name': 'Fee Summary',
                     },
            'report_type': 'xlsx',
        }

    def get_xlsx_report(self, data, response):
        """Action for create XLXS report for student details"""

        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet('Fee Summary')

        head = workbook.add_format({'bold': True, 'border': 1, 'align': 'center'})
        text = workbook.add_format({'border': 1, 'align': 'center'})
        date_fmt = workbook.add_format({'border': 1, 'num_format': 'yyyy-mm-dd'})

        headers = [
            'Sl No', 'Student', 'Admission No', 'Payment Type',
            'Due Date', 'Invoiced', 'Paid', 'Refunded', 'Outstanding'
        ]
        for col, h in enumerate(headers):
            sheet.write(0, col, h, head)

        query = """
                SELECT
                rp.id AS student_id, rp.name AS student_name,
                rp.admission_no, efi.id AS fee_invoice_id, efi.due_date, efi.payment_type,
                COALESCE(inv.total_invoiced, 0) AS total_invoiced,
                COALESCE(ref.total_refunded, 0) AS total_refunded,
                COALESCE(pay.total_paid, 0) AS total_paid,
                COALESCE(inv.total_invoiced, 0)
                - COALESCE(pay.total_paid, 0)
                - COALESCE(ref.total_refunded, 0) AS outstanding_amount     
            FROM res_partner rp          
            LEFT JOIN education_fee_invoice efi
                ON efi.student_id = rp.id           
            -- 🔹 Total invoiced per fee invoice
            LEFT JOIN (
                SELECT
                    fee_invoice_id,
                    SUM(amount_total) AS total_invoiced
                FROM account_move
                WHERE move_type = 'out_invoice'
                  AND state = 'posted'
                GROUP BY fee_invoice_id
            ) inv ON inv.fee_invoice_id = efi.id
            -- 🔹 Total refunded per fee invoice
            LEFT JOIN (
                SELECT
                    fee_invoice_id,
                    SUM(amount_total) AS total_refunded
                FROM account_move
                WHERE move_type = 'out_refund'
                  AND state = 'posted'
                GROUP BY fee_invoice_id
            ) ref ON ref.fee_invoice_id = efi.id          
            -- 🔹 Total paid per fee invoice
            LEFT JOIN (
                SELECT
                    am.fee_invoice_id, SUM(-aml.balance) AS total_paid
                FROM account_move_line aml JOIN account_move am ON am.id = aml.move_id
                WHERE aml.reconciled = TRUE AND am.state = 'posted'
                GROUP BY am.fee_invoice_id) pay ON pay.fee_invoice_id = efi.id     
            WHERE rp.is_student = TRUE
                """

        if data.get('student_ids'):
            student_ids = data['student_ids']

            if len(student_ids) == 1:
                query += " AND rp.id = %s" % student_ids[0]
            else:
                query += " AND rp.id IN %s" % (tuple(student_ids),)

            # ---------- Payment type ----------
        if data.get('payment_type') and data['payment_type'] != 'all':
            query += " AND efi.payment_type = '%s'" % data['payment_type']

        if data.get('is_refund'):
            query += " AND COALESCE(ref.total_refunded, 0) > 0"

            # ---------- Date filters (REFERENCE STYLE) ----------
        if data.get('date_filter') == 'daily':
            today = date.today()
            query += " AND efi.due_date = '%s'" % today

        elif data.get('date_filter') == 'weekly':
            query += """
                             AND DATE_TRUNC('week', efi.due_date)
                                 = DATE_TRUNC('week', CURRENT_DATE)
                         """

        elif data.get('date_filter') == 'monthly':
            query += """
                             AND DATE_TRUNC('month', efi.due_date)
                                 = DATE_TRUNC('month', CURRENT_DATE)
                         """

        elif data.get('date_filter') == 'custom':
            if data.get('from_date') and not data.get('to_date'):
                query += " AND efi.due_date >= '%s'" % data['from_date']

            elif data.get('to_date') and not data.get('from_date'):
                query += " AND efi.due_date <= '%s'" % data['to_date']

            elif data.get('from_date') and data.get('to_date'):
                query += (
                        " AND efi.due_date BETWEEN '%s' AND '%s'"
                        % (data['from_date'], data['to_date'])
                )
        self.env.cr.execute(query)
        rows = self.env.cr.fetchall()

        sheet.set_column('A:A', 6)  # Sl No
        sheet.set_column('B:B', 15)  # Student
        sheet.set_column('C:C', 18)  # Admission No
        sheet.set_column('D:D', 14)  # Payment Type
        sheet.set_column('E:E', 14)  # Due Date
        sheet.set_column('F:F', 12)  # Invoiced
        sheet.set_column('G:G', 12)  # Paid
        sheet.set_column('H:H', 12)  # Refunded
        sheet.set_column('I:I', 14)  # Outstanding

        row_no = 1

        for i, r in enumerate(rows, start=1):
            sheet.write(row_no, 0, i, text)  # Sl No
            sheet.write(row_no, 1, r[1] or '-', text)  # Student Name
            sheet.write(row_no, 2, r[2] or '-', text)  # Admission No
            sheet.write(row_no, 3, r[5] or '-', text)  # Payment Type
            sheet.write(row_no, 4, r[4] or '-', date_fmt)  # Due Date
            sheet.write(row_no, 5, r[6] or 0.0, text)  # Invoiced
            sheet.write(row_no, 6, r[8] or 0.0, text)  # Paid
            sheet.write(row_no, 7, r[7] or 0.0, text)  # Refunded
            sheet.write(row_no, 8, r[9] or 0.0, text)  # Outstanding

            row_no += 1

        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()