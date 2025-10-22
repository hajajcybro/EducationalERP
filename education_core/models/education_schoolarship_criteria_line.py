from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class EducationScholarshipCriteriaLine(models.Model):
    _name = 'education.scholarship.criteria.line'
    _description = 'Scholarship Eligibility Criteria Line'

    name = fields.Char(string='Criteria', required=True)
