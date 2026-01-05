from odoo import models, api

class RefundReport(models.AbstractModel):
    _name = 'report.education_financial_management.report_refund_summary'

    @api.model
    def _get_report_values(self, docids,data=None):
        print("self")
        query="""SELECT
                rr.id AS refund_id,
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
        report = self.env.cr.fetchall()

        return {
            'doc_ids': docids,
            'doc_model': 'education.refund.request',
            'docs': report,
            'data': data,
        }

