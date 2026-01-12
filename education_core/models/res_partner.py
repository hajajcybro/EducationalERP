# -*- coding: utf-8 -*-
from email.policy import default

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import date

class ResPartner(models.Model):
    """Extend partner to add position role"""
    _inherit = 'res.partner'

    position_role = fields.Selection(
        selection=[('teacher', 'Teacher'), ('student', 'Student')],
        string='Position',
    )
    is_student = fields.Boolean('Student')
    email = fields.Char(string='Email', help='Student email address.')
    phone = fields.Char(string='Phone', help='Student contact number.')
    academic_year_id = fields.Many2one('education.academic.year', string='Academic Year',domain=[('state', '!=', 'closed')],)
    program_id = fields.Many2one('education.program',string='Program')
    admission_no = fields.Char(string='Admission Number',)
    class_id = fields.Many2one('education.class', string='Class')
    current_enrollment_id = fields.Many2one('education.enrollment',
             string='Enrollment ID',readonly=True,
             help='Link to the current enrollment record of the student.'
    )
    roll_no = fields.Char('Roll Number')
    class_teacher_id = fields.Many2one('hr.employee', string='Class Teacher',
                                       domain=[('role', '=', 'teacher')])
    father_name = fields.Char('Father Name')
    mother_name = fields.Char('Mother Name')
    contact_no = fields.Char('Contact Number')
    emergency_phone = fields.Char('Emergency Phone Number')
    current_address = fields.Text('Permanent Address')
    occupation = fields.Char('Occupation', help='Job or business')
    id_no = fields.Char('Aadhar No. / ID No.', help='Government-issued ID number')
    relation = fields.Char(string='Relation', help="Relationship of the guardian to the applicant")
    dob = fields.Date('Date of Birth')
    age = fields.Integer('Age',compute='_compute_age', store=True)
    gender = fields.Selection([
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
    ], string='Gender')
    blood_group = fields.Selection([
        ('a+', 'A+'), ('a-', 'A-'),
        ('b+', 'B+'), ('b-', 'B-'),
        ('ab+', 'AB+'), ('ab-', 'AB-'),
        ('o+', 'O+'), ('o-', 'O-'),
    ], string='Blood Group')
    guardian = fields.Char('Guardian Name')
    stu_category_id = fields.Many2one('education.category',
                               string='Category',
                               help='Assign a category to the student.'
                               )
    document_ids = fields.One2many(
        'education.document',
        'student_id',
        string='Documents',
        help='Documents related to this student'
    )
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company,
        help='Company automatically assigned based on current user.'
    )
    previous_academic = fields.Char('Previous Academic')
    previous_class = fields.Char('Previous Class')
    Year_of_passing = fields.Char('Year Of Passing')
    language = fields.Char('Language / Medium')
    board = fields.Char('Board / University')
    parent_email = fields.Char(string="Parent Email")
    last_missing_doc_mail_date = fields.Date(
        string="Last Missing Document Reminder"
    )
    transportation = fields.Boolean(string='Using transportation facility')
    bus_no = fields.Char(string='Bus NO')

    def action_open_documents(self):
        """Open documents related to this student."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Documents',
            'res_model': 'education.document',
            'view_mode': 'list,form',
            'domain': [('admission_no', '=', self.admission_no)],
            'context': {'default_admission_no': self.admission_no},
        }

    def action_open_enrollment(self):
        """Open documents related to this student."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Enrollment Info',
            'res_model': 'education.enrollment',
            'view_mode': 'list,form',
            'domain': [('admission_no', '=', self.admission_no)],
            'context': {'default_admission_no': self.admission_no},
        }

    @api.constrains('class_id')
    def _check_capacity_not_exceeded(self):
        """Prevent exceeding class capacity."""
        for rec in self:
            if len(rec.class_id.student_ids) > rec.class_id.capacity:
                raise ValidationError(_("Class capacity exceeded."))

    @api.model
    def create(self, vals):
        """Override create to assign an admission number when a new student
        is added without one."""
        vals_list = vals if isinstance(vals, list) else [vals]
        for val in vals_list:
            if val.get('is_student') == True and not val.get('admission_no'):
                val['admission_no'] = self.env['ir.sequence'].next_by_code('education_student_admission')
        return super().create(vals_list)

    def write(self, vals):
        """Override write to generate an admission number when a partner
        becomes a student and lacks one."""
        for rec in self:
            if vals.get('is_student') == True and not rec.admission_no:
                vals['admission_no'] = self.env['ir.sequence'].next_by_code('education_student_admission')
        return super().write(vals)

    @api.depends('dob')
    def _compute_age(self):
        """Compute age from date of birth."""
        for rec in self:
            rec.age = int((date.today() - rec.dob).days / 365.25) if rec.dob else 0

    @api.constrains('program_id', 'academic_year_id')
    def _check_duration_match(self):
        """Ensure program duration matches academic year length."""
        for rec in self:
            if rec.program_id and rec.academic_year_id:
                year_diff = (rec.academic_year_id.end_date.year -rec.academic_year_id.start_date.year)
                if rec.program_id.duration != year_diff:
                    raise ValidationError(
                        _("Program duration must match academic year duration.")
                    )

    @api.onchange('class_id')
    def _onchange_class_id(self):
        """Set class teacher and auto-assign next roll number."""
        if self.class_id:
            if self.class_id.class_teacher_id:
                self.class_teacher_id = self.class_id.class_teacher_id
            last_student = self.search([
                ('class_id', '=', self.class_id.id),
                ('roll_no', '!=', False)
            ], order='roll_no desc', limit=1)
            last_roll = int(last_student.roll_no) if last_student and last_student.roll_no else 0
            self.roll_no = last_roll + 1

    def unlink(self):
        for rec in self:
            if rec.is_student:
                old_data = {
                    'Student Name': rec.name,
                    'Admission No': rec.admission_no,
                    'Program': rec.program_id.display_name if rec.program_id else None,
                    'Academic Year': rec.academic_year_id.display_name if rec.academic_year_id else None,
                    'Class': rec.class_id.display_name if rec.class_id else None,
                    'Roll Number': rec.roll_no,
                }
                self.env['education.audit.log'].sudo().create({
                    'user_id': self.env.user.id,
                    'action_type': 'delete',
                    'model_name': rec._name,
                    'record_id': rec.id,
                    'description': 'Student record deleted',
                    'old_values': old_data,
                })
        return super().unlink()




