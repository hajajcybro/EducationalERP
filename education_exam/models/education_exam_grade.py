from odoo import api,models, fields
from odoo.exceptions import ValidationError

class EducationExamGrade(models.Model):
    _name = 'education.exam.grade'
    _description = 'Education Exam Grade'
    _order = 'percentage_from desc'

    name = fields.Char(string='Grade', required=True)
    percentage_from = fields.Float(
        string='Percentage From (%)',
        required=True
    )

    percentage_to = fields.Float(
        string='Percentage To (%)',
        required=True
    )

    remark = fields.Char(string='Description')
    active = fields.Boolean(
        default=True
    )

    @api.constrains('percentage_from', 'percentage_to')
    def _check_percentage_range(self):
        for rec in self:
            if rec.percentage_from < 0 or rec.percentage_to > 100:
                raise ValidationError("Percentage must be between 0 and 100.")
            if rec.percentage_from >= rec.percentage_to:
                raise ValidationError(
                    "'Percentage From' must be less than 'Percentage To'."
                )
