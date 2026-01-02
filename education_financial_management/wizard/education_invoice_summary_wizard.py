# -*- coding: utf-8 -*-
from odoo import models, fields
from datetime import date
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

