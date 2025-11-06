from odoo import models, fields, api

class EducationProgram(models.Model):
    _name = 'education.program'
    _description = 'Education Program'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string="Program Name", required=True)
    code = fields.Char(string="Code", required=True)
    duration = fields.Integer(string="Duration")
    credit_hours = fields.Float(string="Total Credit Hours")
    description = fields.Text(string="Description")
    active = fields.Boolean(default=True, string="Active")
    session_ids = fields.One2many('education.session','program_id', string='Session')

    _sql_constraints = [
        ('unique_program_code', 'unique(code)', 'Program code must be unique!'),
    ]
