from odoo import models, fields

class ScholarshipWizard(models.TransientModel):
    _name = 'scholarship.wizard'
    _description = 'Scholarship Wizard'


    academic_year_id = fields.Many2one(
        'education.academic.year',
        string='Academic Year'
    )
    session_id = fields.Many2one(
        'education.session',
        string='Semester / Session'
    )
    program_id = fields.Many2one(
        'education.program',
        string='Program'
    )
    scholarship_id = fields.Many2one(
        'education.scholarship',
        string='Scholarship'
    )
    application_duration = fields.Selection([
        ('one_time', 'One-time'),
        ('per_semester', 'Per Semester'),
        ('per_year', 'Per Academic Year'),
        ('recurring', 'Recurring'),
    ], string='Application Duration')
    application_state = fields.Selection([
        ('submitted', 'Submitted'),
        ('under_review', 'Under Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ], string='Application Status', default='approved')
    date_from = fields.Date(string='Application Date From')
    date_to = fields.Date(string='Application Date To')
    student_id = fields.Many2one(
        'res.partner',
        string='Student',
        domain=[('is_student', '=', True)]
    )
    has_remaining_amount = fields.Selection([
        ('yes', 'Has Remaining Amount'),
        ('no', 'No Remaining Amount'),
    ], string='Remaining Scholarship')

    # def action_generate_scholarship_report(self):
    #     """Create button action for pdf report"""
    #     # print(self.read())
    #     data = {
    #         'choice': self.choice,
    #         'academic_year_id': self.academic_year_id,
    #         'session_id': self.session_id,
    #         'program_id': self.program_id,
    #         'scholarship_id': self.scholarship_id,
    #         'application_duration': self.application_duration,
    #         'application_state': self.application_state,
    #         'date_from': self.date_from,
    #         'date_to': self.date_to,
    #         'student_id': self.student_id,
    #         'has_remaining_amount': self.has_remaining_amount,
    #     }
    #     print(data)
    #     return self.env.ref('education_scholarship.action_report_scholarship_information').report_action(None, data=data)
    #
