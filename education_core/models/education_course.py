from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


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

    course_type = fields.Selection([
        ('semester', 'Semester-based'),
        ('credit_hour', 'Credit Hour-based'),
    ], string='Course Type', default='semester', required=True)

    _uniq_course_code = models.Constraint(
        'unique(code)','Course code must be unique',
    )

    @api.constrains('duration')
    def _check_duration(self):
        """Validate course duration is positive."""
        for record in self:
            if record.duration and record.duration <= 0:
                raise ValidationError(_("Duration must be a positive value."))

    @api.constrains('credit_hours', 'course_type')
    def _check_credit_hours(self):
        """Ensure credit hours are set for credit-hour courses."""
        for record in self:
            if record.course_type == 'credit_hour' and not record.credit_hours:
                raise ValidationError("Credit hours must be specified for credit hour-based courses.")