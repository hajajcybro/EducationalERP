from odoo import models, fields, api

class EducationCourse(models.Model):
    _name = 'education.course'
    _description = 'Education Course'


    name = fields.Char(string="Course Name", required=True)
    code = fields.Char(string="Course Code", required=True)
    program_id = fields.Many2one('education.program', string="Program", required=True, ondelete='cascade')
    duration = fields.Integer(string="Duration (Months)")
    credit_hours = fields.Float(string="Credit Hours")
    is_elective = fields.Boolean(string="Is Elective?", default=False)
    description = fields.Text(string="Description")
    active = fields.Boolean(default=True, string="Active")

    _sql_constraints = [
        ('unique_course_code', 'unique(code)', 'Course code must be unique!'),
    ]

    @api.constrains('duration')
    def _check_duration(self):
        for record in self:
            if record.duration and record.duration <= 0:
                raise ValueError("Duration must be a positive value.")
