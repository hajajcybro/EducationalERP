# -*- coding: UTF-8 -*-
from odoo import models, api
from datetime import date

class FeeSummaryReport(models.AbstractModel):
    _name = 'report.education_financial_management.report_fee_summary'

    @api.model
    def _get_report_values(self, docids, data=None):
        print("get report !")
        query="""
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
        print(query)

        # ---------- Student filter ----------
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
        records = self.env.cr.dictfetchall()
        return {
            'doc_ids': docids,
            'doc_model': 'education.fee.invoice',
            'docs': records,
            'data': data,
        }

