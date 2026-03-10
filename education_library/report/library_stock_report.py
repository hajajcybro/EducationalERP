# -*- coding: utf-8 -*-
from odoo import models, api


class LibraryStockReport(models.AbstractModel):
    _name = 'report.education_library.report_library_stock'
    _description = 'Library Stock Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        """Generate report values for library stock"""

        query = """
            SELECT 
                elb.id,
                elb.name,
                elb.isbn,
                elb.title,
                elb.authors,
                elb.publisher,
                elc.name AS category_name,
                elb.copies_total,
                elb.copies_available,
                elb.copies_issued
            FROM education_library_book elb
            LEFT JOIN education_library_category elc ON elb.category_id = elc.id
            WHERE 1=1
        """

        params = []

        if data:
            category_ids = data.get('filters', {}).get('categories', [])
            if category_ids:
                placeholders = ','.join(['%s'] * len(category_ids))
                query += " AND elb.category_id IN (%s)" % placeholders
                params.extend(category_ids)

            book_ids = data.get('filters', {}).get('books', [])
            if book_ids:
                placeholders = ','.join(['%s'] * len(book_ids))
                query += " AND elb.id IN (%s)" % placeholders
                params.extend(book_ids)

            authors = data.get('filters', {}).get('authors', '')
            if authors:
                query += " AND elb.authors ILIKE %s"
                params.append('%' + authors + '%')

            publisher = data.get('filters', {}).get('publisher', '')
            if publisher:
                query += " AND elb.publisher ILIKE %s"
                params.append('%' + publisher + '%')

            availability_filter = data.get('filters', {}).get('availability_filter', 'all')
            if availability_filter == 'available':
                query += " AND elb.copies_available > 0"
            elif availability_filter == 'issued':
                query += " AND elb.copies_issued > 0"
            elif availability_filter == 'unavailable':
                query += " AND elb.copies_available = 0"

        query += " ORDER BY elb.title ASC"

        self.env.cr.execute(query, params)
        records = self.env.cr.dictfetchall()

        return {
            'doc_ids': docids,
            'doc_model': 'library.stock.wizard',
            'docs': records,
            'data': data,
        }