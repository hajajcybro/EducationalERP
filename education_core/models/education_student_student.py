# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from datetime import date


class EducationStudentStudent(models.Model):
    _name = 'education.student.student'
    _description = 'Student'
    _inherit = 'mail.thread'
    _order = 'admission_no'


    name = fields.Char('Student Name',
            required = True,
            help = 'Enter the full name of the student.'
    )
    reference_no = fields.Char(
        copy=False, readonly=True,
        tracking=True, default='New',
        help = 'Automatically generated reference number for the student.'

    )
    admission_no = fields.Char(
        string='Admission Number',
        readonly=True,
        copy=False,
        help='Unique admission number assigned to the student.'
    )
    admission_date = fields.Date(
        string='Admission Date',
        default=fields.Date.today,
        readonly=True,
    )
    dob = fields.Date(
        string='Date of Birth', required=True,
        help='Student date of birth.'
    )
    age = fields.Integer('Age',
        compute='_compute_age',
        store=True, readonly=True,
        help='Automatically computed age based on Date of Birth.'
    )
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
    category = fields.Many2one('education.category',
        string='Category',
        help='Assign a category to the student.'
    )
    current_enrollment_id = fields.Many2one('education.enrollment',
        string='Current Enrollment',
        readonly=True,
        help='Link to the current enrollment record of the student.'
    )
    guardian = fields.Char(
        string='Guardians',
        help='Enter the student’s guardians or parents.'

    )
    photo = fields.Binary(string='Image',
                          help='Upload a photo of the student.'
                          )
    state = fields.Selection([
        ('draft', 'Draft'),
        ('registered', 'Registered'),
        ('enrolled', 'Enrolled'),
        ('graduated', 'Graduated'),
        ('left', 'Left'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='draft', help='Current status of the student.'
    )
    notes = fields.Text(string='Notes',help='Additional notes about the student.')

    active = fields.Boolean(default=True, help='Uncheck to archive the student record.')

    email = fields.Char(string='Email', required=True, help='Student email address.')
    phone = fields.Char(string='Phone', help='Student contact number.')

    street = fields.Char('Street', help='Street address.',required=True,)
    street2 = fields.Char('Street2', help='Additional street information.',required=True,)
    city = fields.Char('City', help='City of residence.')
    country_id = fields.Many2one('res.country', string='Country', help='Select the country.')
    state_id = fields.Many2one('res.country.state', 'Fed. State', domain="[('country_id', '=?', country_id)]", help='Select the state or province.')
    country_code = fields.Char(
        related='country_id.code',
        string='Country Code',
        readonly=True,
        help='ISO code of the selected country.'
    )
    zip = fields.Char(string='Zip', help='Postal/zip code.')
    document_ids = fields.One2many(
        'education.document',
        'student_id',
        string='Documents'
    )
    academic_year = fields.Many2one('education.academic.year',string='Academic Year',
                                    domain=[('state', '!=', 'closed')],
                                    )

    def action_open_documents(self):
        """Open documents related to this student."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Documents',
            'res_model': 'education.document',
            'view_mode': 'list,form',
            'domain': [('student_id', '=', self.id)],
            'context': {'default_student_id': self.id},
        }

    @api.depends('dob')
    def _compute_age(self):
        for record in self:
            if record.dob:
                record.age = (date.today() - record.dob).days / 365
                if record.age <= 5:
                    raise ValidationError('Please enter valid Date Of Birth')

    @api.model_create_multi
    def create(self, vals_list):
        """Assign temporary reference number before registration"""
        for vals in vals_list:
            if vals.get('reference_no', _('New')) == _('New'):
                vals['reference_no'] = self.env['ir.sequence'].next_by_code('education_student_temporary') or _('New')
        return super().create(vals_list)

    def action_register(self):
        """Register student and create enrollment record."""
        for rec in self:
            if rec.reference_no and not rec.admission_no:
                rec.admission_no = self.env['ir.sequence'].next_by_code('education_student_admission')
                rec.reference_no = False
                rec.state = 'registered'
                # Create related enrollment record
                # enrollment = self.env['education.enrollment'].create({
                #     'student_id': rec.id,
                #     'current_class_id': '',
                #     'status': 'draft',
                #     'enrollment_date': fields.Date.today(),
                # })
                # rec.current_enrollment_id = enrollment.id

    @api.constrains('email', 'phone')
    def _check_contact_fields(self):
        """Validate email and phone formats."""
        import re
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        phone_pattern = r'^\+?\d{7,15}$'

        for record in self:
            if record.email and not re.match(email_pattern, record.email):
                raise ValidationError(_('Invalid email address. Please enter a valid format like name@example.com.'))
            if record.phone and not re.match(phone_pattern, record.phone):
                raise ValidationError(_('Invalid phone number. Please enter digits only, 7–15 numbers, with optional +.'))

    def action_enroll(self):
        """Open Enrollment form for this student"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Enroll Student',
            'res_model': 'education.enrollment',
            'view_mode': 'form',
            'target': 'current',
            'context': {
                'default_student_id': self.id,
                'default_status': 'enrolled',
            },
        }



