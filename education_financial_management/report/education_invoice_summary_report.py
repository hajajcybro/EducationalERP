from odoo import models, api
from datetime import date

class InvoiceSummary(models.AbstractModel):
    _name = 'report.education_financial_management.report_invoice_summary'

    @api.model
    def _get_report_values(self, docids, data=None):
        print("self")
        query="""
                    SELECT
                am.id AS invoice_id,
                rp.name AS student_name,
                rp.admission_no,
                am.name AS invoice_number,
                am.move_type,
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
              AND rp.is_student = TRUE"""

        # ---------- Student filter ----------
        if data.get('student_ids'):
            student_ids = tuple(data['student_ids'])
            if len(student_ids) == 1:
                query += " AND rp.id = %s" % student_ids[0]
            else:
                query += " AND rp.id IN %s" % (student_ids,)

        # ---------- Invoice type ----------
        if data.get('invoice_type') and data['invoice_type'] != 'all':
            query += " AND am.move_type = '%s'" % data['invoice_type']

        # ---------- Payment state ----------
        if data.get('payment_state') and data['payment_state'] != 'all':
            query += " AND am.payment_state = '%s'" % data['payment_state']

        # ---------- Date filters ----------
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

        self.env.cr.execute(query)
        records = self.env.cr.dictfetchall()

        return {
            'doc_ids' : docids,
            'doc_model' : 'account.move',
            'docs' : records,
            'data' : data,
        }
