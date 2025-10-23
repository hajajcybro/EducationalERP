# -*- coding: utf-8 -*-
from odoo import models, fields

class ResPartner(models.Model):
    """Extend partner to add position role"""
    _inherit = 'res.partner'

    position_role = fields.Selection(
        selection=[('teacher', 'Teacher'), ('student', 'Student')],
        string='Position',
        default=False,  # optional, avoids issues with existing records
    )
