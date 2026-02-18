# -*- coding: utf-8 -*-
from odoo import models, api


class LibraryOverdueReport(models.AbstractModel):
    _name = 'report.education_library.report_library_overdue'
    _description = 'Library Overdue Books Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        """Generate report values for overdue books"""

        query = """
            SELECT 
                elt.id,
                elt.name AS transaction_no,
                elb.title AS book_title,
                elm.name AS member_name,
                elt.issue_date,
                elt.due_date,
                elt.days_overdue,
                elt.fine_amount,
                elt.status
            FROM education_library_transaction elt
            LEFT JOIN education_library_book elb ON elt.book_id = elb.id
            LEFT JOIN education_library_member elm ON elt.member_id = elm.id
            WHERE elt.status = 'overdue'
        """

        params = []

        if data:
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

            date_from = data.get('filters', {}).get('date_from')
            if date_from:
                query += " AND elt.issue_date >= %s"
                params.append(date_from)

            date_to = data.get('filters', {}).get('date_to')
            if date_to:
                query += " AND elt.issue_date <= %s"
                params.append(date_to)

        query += " ORDER BY elt.due_date ASC"

        self.env.cr.execute(query, params)
        records = self.env.cr.dictfetchall()

        return {
            'doc_ids': docids,
            'doc_model': 'library.overdue.wizard',
            'docs': records,
            'data': data,
        }