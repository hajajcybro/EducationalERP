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
    application_duration = fields.Selection([
        ('one_time', 'One-time'),
        ('per_semester', 'Per Semester'),
        ('per_year', 'Per Academic Year'),
        ('recurring', 'Recurring (Every Payment)'),
    ], required=True, default='one_time')
    approved_student_ids = fields.One2many(
        'education.scholarship.application',
        'scholarship_id',
        string='Approved Students',
        domain=[('state', '=', 'approved')]
    )

    def action_open(self):
        for record in self:
            record.status = 'open'
        students = self.env['res.partner'].sudo().search([
            ('position_role', '=', 'student'),
            ('active', '=', True),
        ])
        if students:
            recipient_ids = [(4, s.id) for s in students]
            notif = self.env['edu.notification'].sudo().create({
                'name': f'New Scholarship: {self.name}',
                'message': (
                    f'A new scholarship "{self.name}" is now open for applications. '
                    f'Please check the Published Scholarships section.'
                ),
                'recipient_ids': recipient_ids,
                'module': 'scholarship',
                'notification_type': 'in_app',
                'status': 'draft',
            })
            notif.action_send()

    def action_expire(self):
        for record in self:
            record.status = 'expired'

