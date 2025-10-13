from odoo import models, fields, api

class EducationProgram(models.Model):
    _name = 'education.program'
    _description = 'Education Program'
    _rec_name = 'name'

    name = fields.Char(string="Program Name", required=True)
    code = fields.Char(string="Code", required=True)
    duration = fields.Integer(string="Duration (Years)")
    credit_hours = fields.Float(string="Total Credit Hours")
    description = fields.Text(string="Description")
    active = fields.Boolean(default=True, string="Active")
    course_ids = fields.One2many('education.course', 'program_id', string="Courses")

    _sql_constraints = [
        ('unique_program_code', 'unique(code)', 'Program code must be unique!'),
    ]

    @api.constrains('duration')
    def _check_duration(self):
        for record in self:
            if record.duration and record.duration <= 0:
                raise ValueError("Duration must be a positive value.")
