from odoo import models, fields

class EducationDocument(models.Model):
    _inherit = 'education.document'

    faculty_id = fields.Many2one(
        'hr.employee',
        string='Faculty'
    )

    program_id = fields.Many2one(
        'education.program',
        string='Program'
    )

    uploaded_by = fields.Many2one(
        'res.users',
        default=lambda self: self.env.user,
    )

    upload_date = fields.Datetime(
        default=fields.Datetime.now,
        readonly=True
    )
    version = fields.Integer(
        default=1,
        tracking=True
    )
    # expiry handle
    is_expired = fields.Boolean(
        string="Expired",
        compute="_compute_is_expired",
        store=True
    )
    validity_days = fields.Integer(
        string="Validity (Days)",
        help="Used only when expiry type is duration-based"
    )
    expiry_date = fields.Date(
        string="Expiry Date"
    )


