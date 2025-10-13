from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class EducationScholarshipCriteria(models.Model):
    _name = 'education.scholarship.criteria'
    _description = 'Scholarship Eligibility Criteria'

    name = fields.Char(string='Criteria Name', required=True)
    criteria_field = fields.Selection([
        ('grade', 'Minimum Grade'),
        ('income', 'Maximum Family Income'),
        ('attendance', 'Minimum Attendance (%)'),
        ('gender', 'Gender'),
        ('nationality', 'Nationality'),
    ], string='Field', required=True)
    operator = fields.Selection([
        ('>=', 'Greater than or equal to'),
        ('<=', 'Less than or equal to'),
        ('==', 'Equal to'),
    ], string='Operator', required=True, default='>=')
    value = fields.Char(string='Value', required=True)
    description = fields.Char(string='Description')

    def check_eligibility(self, student):
        """Perform validation on student record"""
        for record in self:
            if record.criteria_field == 'grade':
                if not student.grade or not float(student.grade) >= float(record.value):
                    raise ValidationError(_(f"Student does not meet minimum grade requirement ({record.value}%)"))
            elif record.criteria_field == 'income':
                if not student.family_income or not float(student.family_income) <= float(record.value):
                    raise ValidationError(_(f"Student exceeds maximum family income limit ({record.value})"))
            elif record.criteria_field == 'attendance':
                if not student.attendance or not float(student.attendance) >= float(record.value):
                    raise ValidationError(_(f"Student does not meet attendance requirement ({record.value}%)"))
            elif record.criteria_field == 'gender':
                if student.gender != record.value:
                    raise ValidationError(_(f"Scholarship is available only for {record.value} students."))
            elif record.criteria_field == 'nationality':
                if student.nationality != record.value:
                    raise ValidationError(_(f"Scholarship is available only for {record.value} nationality."))
