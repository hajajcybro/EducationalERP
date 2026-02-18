# -*- coding: utf-8 -*-
from odoo import models, api


class LibraryUsageReport(models.AbstractModel):
    _name = 'report.education_library.report_library_usage'
    _description = 'Library Usage Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        """Generate report values for library usage"""

        query = """
            SELECT 
                elt.id,
                elt.name AS transaction_no,
                elb.title AS book_title,
                elb.authors,
                elb.isbn,
                elm.name AS member_name,
                elm.member_type,
                elt.issue_date,
                elt.due_date,
                elt.return_date,
                elt.days_overdue,
                elt.fine_amount,
                elt.renewal_count,
                elt.status
            FROM education_library_transaction elt
            LEFT JOIN education_library_book elb ON elt.book_id = elb.id
            LEFT JOIN education_library_member elm ON elt.member_id = elm.id
            WHERE 1=1
        """

        params = []

        if data:
            if data.get('date_from'):
                query += " AND elt.issue_date >= %s"
                params.append(data.get('date_from'))

            if data.get('date_to'):
                query += " AND elt.issue_date <= %s"
                params.append(data.get('date_to'))

            book_ids = data.get('filters', {}).get('books', [])
            if book_ids:
                placeholders = ','.join(['%s'] * len(book_ids))
                query += " AND elt.book_id IN (%s)" % placeholders
                params.extend(book_ids)

            member_ids = data.get('filters', {}).get('members', [])
            if member_ids:
                placeholders = ','.join(['%s'] * len(member_ids))
                query += " AND elt.member_id IN (%s)" % placeholders
                params.extend(member_ids)

            member_type = data.get('filters', {}).get('member_type', '')
            if member_type:
                query += " AND elm.member_type = %s"
                params.append(member_type)

        query += " ORDER BY elt.issue_date DESC"

        self.env.cr.execute(query, params)
        records = self.env.cr.dictfetchall()

        return {
            'doc_ids': docids,
            'doc_model': 'library.usage.report.wizard',
            'docs': records,
            'data': data,
        }