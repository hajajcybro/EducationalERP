# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import json
import io
import xlsxwriter
from odoo.tools import json_default


class LibraryStockWizard(models.TransientModel):
    _name = 'library.stock.wizard'
    _description = 'Library Stock Report Wizard'

    book_ids = fields.Many2many(
        comodel_name='education.library.book',
        string='Books',
        help='Select specific books to include in the report. Leave empty for all books.'
    )

    category_ids = fields.Many2many(
        comodel_name='education.library.category',
        string='Categories',
        help='Select specific categories to include in the report. Leave empty for all categories.'
    )

    authors = fields.Char(
        string='Authors',
        help='Filter books by author name (partial match). Leave empty to include all authors.'
    )

    publisher = fields.Char(
        string='Publisher',
        help='Filter books by publisher name (partial match). Leave empty to include all publishers.'
    )

    availability_filter = fields.Selection(
        selection=[
            ('all', 'All Books'),
            ('available', 'Only Available Copies'),
            ('issued', 'Only Issued Copies'),
            ('unavailable', 'No Available Copies'),
        ],
        string='Availability Filter',
        default='all',
        help='Filter books based on availability status.'
    )

    def action_generate_pdf(self):
        """Generate PDF report"""
        self.ensure_one()

        return self.env.ref('education_library.action_report_stock').report_action(
            self.ids,
            data={
                'filters': {
                    'books': self.book_ids.ids if self.book_ids else [],
                    'categories': self.category_ids.ids if self.category_ids else [],
                    'authors': self.authors or '',
                    'publisher': self.publisher or '',
                    'availability_filter': self.availability_filter,
                }
            }
        )

    def action_generate_xlsx(self):
        """Generate XLSX report"""
        self.ensure_one()

        data = {
            'books': self.book_ids.ids if self.book_ids else [],
            'categories': self.category_ids.ids if self.category_ids else [],
            'authors': self.authors or '',
            'publisher': self.publisher or '',
            'availability_filter': self.availability_filter,
        }

        return {
            'type': 'ir.actions.report',
            'data': {
                'model': 'library.stock.wizard',
                'options': json.dumps(data, default=json_default),
                'output_format': 'xlsx',
                'report_name': 'Library Stock Report',
            },
            'report_type': 'xlsx',
        }

    def get_xlsx_report(self, data, response):
        """Generate XLSX file"""
        books = self.env['education.library.book'].search([])

        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet("Library Stock Report")

        header_format = workbook.add_format({
            'bold': True, 'font_size': 12, 'align': 'center', 'valign': 'vcenter',
            'bg_color': '#aca2a0', 'font_color': 'white', 'border': 1
        })

        cell_format = workbook.add_format({
            'align': 'left', 'valign': 'vcenter', 'border': 1, 'font_size': 10
        })

        number_format = workbook.add_format({
            'align': 'center', 'valign': 'vcenter', 'border': 1, 'font_size': 10
        })

        column_widths = [12, 25, 20, 15, 12, 12, 12, 12]
        for col, width in enumerate(column_widths):
            sheet.set_column(col, col, width)

        sheet.freeze_panes(4, 0)

        row = 0

        title_format = workbook.add_format({
            'bold': True, 'font_size': 14, 'align': 'left'
        })
        sheet.write(row, 0, 'Library Stock Report', title_format)
        row += 1

        date_info_format = workbook.add_format({
            'font_size': 10, 'align': 'left'
        })
        sheet.write(row, 0, f"Report Generated On: {fields.Date.today()}", date_info_format)
        row += 2

        headers = [
            'ISBN', 'Book Title', 'Authors', 'Publisher', 'Category',
            'Total Copies', 'Available', 'Issued'
        ]

        for col, header in enumerate(headers):
            sheet.write(row, col, header, header_format)
        row += 1

        for book in books:
            sheet.write(row, 0, book.isbn or '', cell_format)
            sheet.write(row, 1, book.title, cell_format)
            sheet.write(row, 2, book.authors or '', cell_format)
            sheet.write(row, 3, book.publisher or '', cell_format)
            sheet.write(row, 4, book.category_id.name if book.category_id else '', cell_format)
            sheet.write(row, 5, book.copies_total, number_format)
            sheet.write(row, 6, book.copies_available, number_format)
            sheet.write(row, 7, book.copies_issued, number_format)
            row += 1

        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()