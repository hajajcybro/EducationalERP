# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import json
import io
import xlsxwriter
from odoo.tools import json_default


class LibraryUsageReportWizard(models.TransientModel):
    _name = 'library.usage.report.wizard'
    _description = 'Library Usage Report Wizard'

    book_ids = fields.Many2many(comodel_name='education.library.book',string='Books',
        help='Select specific books to include in the report. Leave empty for all books.'
    )
    member_ids = fields.Many2many(comodel_name='education.library.member',string='Members',
        help='Select specific members to include in the report. Leave empty for all members.'
    )
    member_types = fields.Selection(
        selection=[
            ('student', 'Student'),
            ('faculty', 'Faculty'),
            ('staff', 'Staff'),
            ('external', 'External')
        ],
        string='Member Type',
        help='Select a specific member type to filter by.'
    )
    date_from = fields.Date(string='Date From',help='Start date for the report period. Leave empty to include all data.')
    date_to = fields.Date(string='Date To',help='End date for the report period. Leave empty to include all data.')

    @api.constrains('date_from', 'date_to')
    def _check_dates(self):
        for wizard in self:
            if wizard.date_from and wizard.date_to and wizard.date_from > wizard.date_to:
                raise ValidationError(_('Date From cannot be after Date To!'))

    def action_generate_pdf(self):
        """Generate PDF report"""
        self.ensure_one()
        domain = [
            ('status', 'in', ['issued', 'returned', 'overdue'])
        ]
        if self.date_from:
            domain.append(('issue_date', '>=', self.date_from))
        if self.date_to:
            domain.append(('issue_date', '<=', self.date_to))
        if self.book_ids:
            domain.append(('book_id', 'in', self.book_ids.ids))
        if self.member_ids:
            domain.append(('member_id', 'in', self.member_ids.ids))
        elif self.member_types:
            members = self.env['education.library.member'].search([
                ('member_type', '=', self.member_types)
            ])
            domain.append(('member_id', 'in', members.ids))

        transactions = self.env['education.library.transaction'].search(domain)

        if not transactions:
            raise ValidationError(_('No transactions found for the selected criteria!'))

        return self.env.ref('education_library.action_report_usage').report_action(
            self.ids,
            data={
                'date_from': self.date_from,
                'date_to': self.date_to,
                'filters': {
                    'books': self.book_ids.ids if self.book_ids else [],
                    'members': self.member_ids.ids if self.member_ids else [],
                    'member_type': self.member_types or '',
                }
            }
        )

    def action_generate_xlsx(self):
        """Generate XLSX report"""
        self.ensure_one()

        data = {
            'date_from': self.date_from.isoformat() if self.date_from else None,
            'date_to': self.date_to.isoformat() if self.date_to else None,
            'filters': {
                'books': self.book_ids.ids if self.book_ids else [],
                'members': self.member_ids.ids if self.member_ids else [],
                'member_type': self.member_types or '',
            }
        }

        return {
            'type': 'ir.actions.report',
            'data': {
                'model': 'library.usage.report.wizard',
                'options': json.dumps(data, default=json_default),
                'output_format': 'xlsx',
                'report_name': 'Library Usage Report',
            },
            'report_type': 'xlsx',
        }

    def get_xlsx_report(self, data, response):
        """Generate XLSX file"""
        report_model = self.env['report.education_library.report_library_usage']
        values = report_model._get_report_values([], data=data)
        records = values.get('docs', [])

        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet("Library Usage Report")

        header_format = workbook.add_format({
            'bold': True,'font_size': 12,'align': 'center','valign': 'vcenter',
            'bg_color': '#aca2a0','font_color': 'white','border': 1
        })

        cell_format = workbook.add_format({
            'align': 'left','valign': 'vcenter','border': 1,'font_size': 10
        })

        currency_format = workbook.add_format({
            'align': 'right','valign': 'vcenter','border': 1,
            'font_size': 10,'num_format': '0.00'
        })

        date_format = workbook.add_format({
            'align': 'center','valign': 'vcenter','border': 1,'font_size': 10,'num_format': 'yyyy-mm-dd'
        })

        column_widths = [12, 25, 20, 15, 12, 12, 12, 12, 12, 12]
        for col, width in enumerate(column_widths):
            sheet.set_column(col, col, width)

        sheet.freeze_panes(4, 0)

        row = 0

        title_format = workbook.add_format({
            'bold': True,'font_size': 14,'align': 'left'
        })
        sheet.write(row, 0, 'Library Usage Report', title_format)
        row += 1

        date_info_format = workbook.add_format({
            'font_size': 10,'align': 'left'
        })
        sheet.write(row, 0, f"Report Period: {data.get('date_from')} to {data.get('date_to')}", date_info_format)
        row += 2

        headers = [
            'Transaction #','Book Title','Member Name','Member Type','Issue Date','Due Date','Return Date','Days Overdue','Fine'
        ]

        for col, header in enumerate(headers):
            sheet.write(row, col, header, header_format)
        row += 1

        for record in records:
            sheet.write(row, 0, record.get('transaction_no', ''), cell_format)
            sheet.write(row, 1, record.get('book_title', ''), cell_format)
            sheet.write(row, 2, record.get('member_name', ''), cell_format)
            sheet.write(row, 3, record.get('member_type', ''), cell_format)
            sheet.write(row, 4, record.get('issue_date', ''), date_format)
            sheet.write(row, 5, record.get('due_date', ''), date_format)
            sheet.write(row, 6, record.get('return_date', '') or 'Not Returned', date_format)
            sheet.write(row, 7, record.get('days_overdue', 0), cell_format)
            sheet.write(row, 8, float(record.get('fine_amount', 0) or 0), currency_format)
            row += 1

        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()