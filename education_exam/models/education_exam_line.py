from odoo import api, fields, models
from odoo.exceptions import  ValidationError


class EducationExamLine(models.Model):
    """Model for adding subjects in examination"""

    _name = 'education.exam.line'
    _description = 'Subjects'

    course_id = fields.Many2one(
        'education.subject', string='Course', required=True,
        help='Course associated with the subject line.')
    date = fields.Date(
        string='Date', required=True,
        help='Date of examination.')
    time_from = fields.Float(
        string='Time From', required=True, help='Start time of Exam.')
    time_to = fields.Float(
        string='Time To', required=True, help='End time of the Exam.')
    max_marks = fields.Integer(
        string='Mark',required=True, help='Maximum Marks.')
    exam_id = fields.Many2one(
        'education.exam', string='Exam',
        help='Exam associated with the subject line.')
    weightage = fields.Float(string='Weightage')

    @api.constrains('time_from', 'time_to')
    def _check_exam_time(self):
        for record in self:
            if record.time_from and record.time_to:
                if record.time_from >= record.time_to:
                    raise ValidationError(
                        "Time From must be less than Time To."
                    )

