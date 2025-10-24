from odoo import models, fields, api

class EducationProgram(models.Model):
    _name = 'education.program'
    _description = 'Education Program'

    name = fields.Char(string="Program Name", required=True)
    code = fields.Char(string="Code", required=True)
    duration = fields.Integer(string="Duration")
    credit_hours = fields.Float(string="Total Credit Hours")
    description = fields.Text(string="Description")
    active = fields.Boolean(default=True, string="Active")
    course_ids = fields.One2many('education.course', 'program_id', string="Courses")

    _sql_constraints = [
        ('unique_program_code', 'unique(code)', 'Program code must be unique!'),
    ]
