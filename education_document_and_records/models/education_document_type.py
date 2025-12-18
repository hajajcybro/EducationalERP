from odoo import models, fields


class EducationDocumentType(models.Model):
    _inherit = 'education.document.type'

    # mandatory document manage
    is_mandatory = fields.Boolean(
        string='Mandatory',
        help='Whether this document is mandatory for completion'
    )
    reminder_interval_days = fields.Integer(
        string="Reminder Interval (Days)",
        default=7,
        help="Send reminder after these many days if document is still missing"
    )

    # expiry doc manage
    is_expirable = fields.Boolean(
        string="Has Expiry",
        help="Enable if this document type expires (e.g. Medical Certificate)"
    )
    expiry_mode = fields.Selection(
        [('date', 'Expiry Date'), ('duration', 'Validity Duration')],
        string="Expiry Type"
    )
    validity_days = fields.Integer(
        string="Validity (Days)",
        help="Used only when expiry type is duration-based"
    )



