# -*- coding: utf-8 -*-
from email.policy import default

from odoo import models, fields

class HrEmployee(models.Model):
    """Extend partner to add position role"""
    _inherit = 'hr.employee'

    role = fields.Selection(
        selection=[('teacher', 'Teacher'), ('staff', 'Office Staff'),('driver','Driver'),('other','Other')],
        string='Position',
    )
    other_role = fields.Char('Other Role')
