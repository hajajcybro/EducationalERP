from odoo import models, fields


class EducationDocumentType(models.Model):
    _inherit = 'education.document.type'

    is_mandatory = fields.Boolean(
        string='Mandatory',
        help='Whether this document is mandatory for completion'
    )
    is_expirable = fields.Boolean(
        string="Has Expiry",
        help="Enable if this document type expires (e.g. Medical Certificate)"
    )
    expiry_mode = fields.Selection(
        [('date', 'Expiry Date'), ('duration', 'Validity Duration')],
        string="Expiry Type"
    )



