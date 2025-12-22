from odoo import models, fields, api, _


class MissingDocumentReportWizard(models.TransientModel):
    _name = 'education.document.missing.report.wizard'
    _description = 'Missing / Pending Documents Report Wizard'

    report_type = fields.Selection([
        ('missing', 'Missing Documents'),
        ('pending', 'Pending Uploads'),
    ], string="Report Type", required=True, default='missing')

    document_type_id = fields.Many2one(
        'education.document.type',
        string='Document Type',
        help='Filter by specific document type'
    )

    student_id = fields.Many2one(
        'res.partner',
        string='Student',
        domain=[('is_student', '=', True)]
    )

    only_mandatory = fields.Boolean(
        string="Only Mandatory Documents",
        default=True
    )
