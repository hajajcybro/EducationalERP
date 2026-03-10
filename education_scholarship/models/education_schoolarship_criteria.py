from odoo import models, fields

class EducationScholarshipCriteria(models.Model):
    _name = 'education.scholarship.criteria'
    _description = 'Scholarship Eligibility Criteria'

    name = fields.Char(string='Criteria', required=True)
