from odoo import models, fields, api


class AccountFollowupLine(models.Model):
    _inherit = 'account_followup.followup.line'

    is_student_followup = fields.Boolean(
        string="Student Follow-up"
    )

