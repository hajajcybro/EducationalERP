from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class EducationScholarship(models.Model):
    _name = 'education.scholarship'
    _description = 'Education Scholarship'

    name = fields.Char(string='Scholarship Name', required=True)
    amount = fields.Float(string='Scholarship Amount', required=True)
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
    description =fields.Text(string='Description')

    def action_open(self):
        for record in self:
            record.status = 'open'

    def action_award(self):
        """Validate eligibility before awarding scholarship"""
        for record in self:
            record.status = 'awarded'

    def action_expire(self):
        for record in self:
            record.status = 'expired'
