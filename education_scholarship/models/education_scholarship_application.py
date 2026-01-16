from odoo import models, fields, api
from zeep.exceptions import ValidationError


class EducationScholarshipApplication(models.Model):
    _name = 'education.scholarship.application'
    _description = 'Scholarship Application'
    _rec_name = 'student_id'

    scholarship_id = fields.Many2one(
        'education.scholarship', domain=[('status', '=', 'open')],
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
        ('cancel','Cancel'),
    ], default='draft', string='Status')
    application_date = fields.Date(
        default=fields.Date.today,
        string='Application Date'
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
    exam_result_id = fields.Many2one('education.exam.result',
        string='Exam Result',readonly=True,
        help='Latest exam result of the student'
    )
    description = fields.Text(string='Description')
    document_count = fields.Integer(
        string='Documents',
        compute='_compute_document_count'
    )

    def _compute_document_count(self):
        Document = self.env['education.document']
        for rec in self:
            rec.document_count = Document.search_count([
                ('student_id', '=', rec.student_id.id),
            ])

    def action_submit(self):
        for rec in self:
            rec.state = 'submitted'

    def action_cancel(self):
        for rec in self:
            rec.state = 'cancel'

    def action_review(self):
        for rec in self:
            rec.state = 'under_review'

    def action_open_exam_result(self):
            self.ensure_one()
            if not self.student_id:
                ValidationError('Exam Result cannot be submitted')
            return {
                'type': 'ir.actions.act_window',
                'name': 'Exam Results',
                'res_model': 'education.exam.result',
                'view_mode': 'list,form',
                'domain': [('student_id', '=', self.student_id.id)],
                'context': {
                    'default_student_id': self.student_id.id,
                },
                'target': 'current',
            }

    def action_open_documents(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Student Documents',
            'res_model': 'education.document',
            'view_mode': 'list,form',
            'domain': [
                ('student_id', '=', self.student_id.id),
            ],
            'context': {
                'default_student_id': self.student_id.id,
            }
        }

    @api.onchange('scholarship_id')
    def _onchange_scholarship_description(self):
        for rec in self:
            rec.description = False
            scholarship = rec.scholarship_id
            lines = []
            lines.append(f"Scholarship Name  : {scholarship.name}")
            if scholarship.scholarship_amount:
                lines.append(f"Scholarship Amount  : {scholarship.scholarship_amount}")
            if scholarship.start_date or scholarship.end_date:
                lines.append(f"Validity Period  : {scholarship.start_date} to {scholarship.end_date}")
            if scholarship.academic_year_id:
                lines.append(f"Academic Year  : {scholarship.academic_year_id.name}")
            if scholarship.eligibility_ids:
                lines.append("Eligibility Criteria  :")
                for criteria in scholarship.eligibility_ids:
                    crit_name = criteria.criteria_id.name
                    operator = criteria.operator
                    value = criteria.value
                    lines.append(f"  - {crit_name} {operator} {value}")
                lines.append("IMPORTANT INSTRUCTIONS :")
                lines.append(
                    "Please upload the relevant certificate copies corresponding to this "
                    "scholarship application for verification purposes. "
                    "Incomplete or incorrect documents may lead to rejection."
                )
                rec.description = "<br/>".join(lines)
            rec.description = "\n".join(lines)

    def action_check(self):
        for rec in self:
            if not rec.exam_result_id:
                exam_result = self.env['education.exam.result'].search(
                    [('student_id', '=', rec.student_id.id)],
                    order='id desc',
                    limit=1
                )
                if not exam_result:
                    print("No exam result found")
                    rec.state = 'rejected'
                    return
                rec.exam_result_id = exam_result
            percentage = (rec.exam_result_id.total_mark_scored / rec.exam_result_id.total_max_mark) * 100
            print("PERCENTAGE :", percentage)
            for rule in rec.scholarship_id.eligibility_ids:
                criteria_name = (rule.criteria_id.name or '').lower()
                academic_keywords = ['score', 'mark', 'percentage', '%', 'grade']
                if any(key in criteria_name for key in academic_keywords):
                    required = float(rule.value)
                    operator = rule.operator
                    failed = (
                            (operator == '>' and not percentage > required) or
                            (operator == '>=' and not percentage >= required) or
                            (operator == '<' and not percentage < required) or
                            (operator == '<=' and not percentage <= required) or
                            (operator == '=' and not percentage == required)
                    )
                    if failed:
                        rec.state = 'rejected'
                        return
                rec.state = 'approved'





