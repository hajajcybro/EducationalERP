from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class EducationCourse(models.Model):
    _name = 'education.course'
    _description = 'Education Course'


    name = fields.Char(string="Course Name", required=True)
    code = fields.Char(string="Course Code", required=True)
    program_id = fields.Many2one('education.program', string="Program", required=True, ondelete='cascade')
    duration = fields.Integer(string="Duration (Months)")
    is_elective = fields.Boolean(string="Is Elective?", default=False)
    description = fields.Text(string="Description")
    active = fields.Boolean(default=True, string="Active")

    credit_hours = fields.Float(string="Credit Hours")
    is_credit_hour = fields.Boolean(string="Credit Hour Based?")

    _uniq_course_code = models.Constraint(
        'unique(code)','Course code must be unique',
    )

    @api.constrains('duration')
    def _check_duration(self):
        """Validate course duration is positive."""
        for record in self:
            if record.duration and record.duration <= 0:
                raise ValidationError(_("Duration must be a positive value."))

    @api.constrains('credit_hours', 'is_credit_hour')
    def _check_credit_hours(self):
        for record in self:
            if record.is_credit_hour and not record.credit_hours:
                raise ValidationError(_("Credit hours must be specified when the course is credit-hour based."))
