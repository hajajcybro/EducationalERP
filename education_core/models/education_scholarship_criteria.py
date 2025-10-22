from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class EducationScholarshipCriteria(models.Model):
    _name = 'education.scholarship.criteria'
    _description = 'Scholarship Eligibility Criteria'
    _rec_name = 'criteria'

    criteria = fields.Many2one('education.scholarship.criteria.line', required=True)
    operator = fields.Selection([
        ('>=', 'Greater than or equal to'),
        ('<=', 'Less than or equal to'),
        ('==', 'Equal to'),
    ], default='>=')
    value = fields.Char(string='Value')
