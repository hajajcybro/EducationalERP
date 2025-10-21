from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class EducationScholarship(models.Model):
    _name = 'education.scholarship'
    _description = 'Education Scholarship'

    name = fields.Char(string='Scholarship Name', required=True)
    scholarship_type = fields.Selection([
        ('merit', 'Merit Based'),
        ('need', 'Need Based'),
        ('sports', 'Sports'),
        ('other', 'Other')
    ], string='Scholarship Type', required=True, default='merit')
    amount = fields.Float(string='Scholarship Amount', required=True)
    min_gpa = fields.Float(string='Minimum GPA')
    max_income = fields.Float(string='Maximum Family Income')
    description = fields.Text(string='Description')
    duration = fields.Integer(string='Duration (Months)')
    issue_date = fields.Date(string='Issue Date')
    active = fields.Boolean(default=True)
    eligibility_ids = fields.Many2many(
        'education.scholarship.criteria',
        'education_scholarship_criteria_rel',
        'scholarship_id',
        'criteria_id',
        string='Eligibility Criteria'
    )
    status = fields.Selection([
        ('draft', 'Draft'),
        ('open', 'Open for Application'),
        ('awarded', 'Awarded'),
        ('expired', 'Expired'),
    ], string='Status', default='draft')

    def action_open(self):
        for record in self:
            record.status = 'open'

    def action_award(self):
        """Validate eligibility before awarding scholarship"""
        for record in self:
            student = record.student_id
            if not student:
                raise ValidationError(_("Please select a student to award the scholarship."))

            for criteria in record.eligibility_ids:
                criteria.check_eligibility(student)

            record.status = 'awarded'
            record.issue_date = fields.Date.today()

    def action_expire(self):
        for record in self:
            record.status = 'expired'
