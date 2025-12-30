from odoo import models, fields, api


class AccountFollowupLine(models.Model):
    _inherit = 'account_followup.followup.line'

    custom_note = fields.Char(string="Custom Note")
