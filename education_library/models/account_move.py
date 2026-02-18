# -*- coding: utf-8 -*-
from odoo import api, fields, models

class AccountMove(models.Model):
    _inherit = 'account.move'

    library_member_id = fields.Many2one(comodel_name='education.library.member', string='Library Member', readonly=True)
