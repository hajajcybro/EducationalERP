from odoo import models, fields
from pkg_resources import require


class EducationScholarshipApplication(models.Model):
    _name = 'education.scholarship.application'
    _description = 'Scholarship Application'
    _rec_name = 'student_id'

    scholarship_id = fields.Many2one(
        'education.scholarship',
        string='Scholarship',
    )
    student_id = fields.Many2one(
        'res.partner', required=True,
        string='Student',domain=[('is_student', '=', True)],
    )
    admission_no = fields.Char(
        related='student_id.admission_no', required=True,
        string='Admission Number',
    )
    program_id = fields.Many2one(
        'education.program',
        related='student_id.program_id',
        string='Program',
    )
    semester = fields.Many2one(
        'education.session',
        related='student_id.class_id.session_id',
        string='Semester / Medium',
    )
    academic_year_id = fields.Many2one(
        'education.academic.year',
        related='student_id.academic_year_id',
        string='Academic Year',
    )
    category_id = fields.Many2one(
        'education.category',
        related='student_id.stu_category_id',
        string='Category',
    )
    contact_email = fields.Char(
        related='student_id.email',
        string='Email',
    )
    contact_phone = fields.Char(
        related='student_id.phone',
        string='Phone',
    )
    state = fields.Selection([
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('under_review', 'Under Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ], default='draft', string='Status')
    application_date = fields.Date(
        default=fields.Date.today,
        string='Application Date'
    )
    document_type= fields.Many2many(
        'education.document.type',
    )
    bank_name = fields.Char(string='Bank Name',  related='student_id.bank_name',
                            help='Select an approved bank'
                            )
    bank_branch = fields.Char(
        string='Branch Name', related='student_id.bank_branch',
    )
    account_holder_name = fields.Char(
        string='Account Holder Name', related='student_id.account_holder_name',
        help='Must match student or parent name'
    )
    bank_account_number = fields.Char(
        string='Account Number',related='student_id.bank_account_number',
    )
    account_type = fields.Selection([
        ('savings', 'Savings'),
        ('current', 'Current'),
    ], string='Account Type', default='savings')
    ifsc_code = fields.Char(
        string='IFSC Code',related='student_id.ifsc_code',
        help='For Indian banks'
    )
    swift_code = fields.Char(
        string='SWIFT Code',related='student_id.swift_code',
        help='For international banks'
    )
    bank_address = fields.Text(
        string='Bank Address',related='student_id.bank_address',
    )

    def action_submit(self):
        for rec in self:
            rec.state = 'submitted'
