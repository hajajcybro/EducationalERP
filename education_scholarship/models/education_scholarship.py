from odoo import models, fields

class EducationScholarship(models.Model):
    _name = 'education.scholarship'
    _description = 'Education Scholarship'

    name = fields.Char(string='Scholarship Name', required=True)
    scholarship_amount = fields.Float(string='Scholarship Amount', required=True)
    active = fields.Boolean(default=True)
    number_of_awards = fields.Float(string='Number of Awards',
            help="Maximum number of students who can receive this scholarship (0 = unlimited).")
    start_date = fields.Date(string='Start Date')
    end_date = fields.Date(string='End Date')
    academic_year_id = fields.Many2one('education.academic.year',string='Academic Year',help='Academic Year - When it applies')
    eligibility_ids = fields.Many2many(
        'education.eligibility.criteria',
        'education_scholarship_criteria_rel',
        'scholarship_id',
        'criteria_id',
        string='Eligibility Criteria'
    )
    document_type_ids = fields.Many2many(
        'education.document.type',
    )
    status = fields.Selection([
        ('draft', 'Draft'),
        ('open', 'Open for Application'),
        ('expired', 'Expired'),
    ], string='Status', default='draft')
    description =fields.Text(string='Description')

    def action_open(self):
        for record in self:
            record.status = 'open'

    def action_expire(self):
        for record in self:
            record.status = 'expired'

