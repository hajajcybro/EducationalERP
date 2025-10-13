# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from datetime import date


class EducationStudentStudent(models.Model):
    _name = 'education.student.student'
    _description = 'Student'
    _inherit = 'mail.thread'
    _rec_name = 'admission_no'
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
        ('applied', 'Applied'),
        ('admitted', 'Admitted'),
        ('enrolled', 'Enrolled'),
        ('graduated', 'Graduated'),
        ('left', 'Left'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='draft', help='Current status of the student.'
    )

    notes = fields.Text(string='Notes',help='Additional notes about the student.')
    created_by = fields.Many2one(
        'res.users',
        string='Created By',
        readonly=True,
        default=lambda self: self.env.user,
        help='User who created the student record.'
    )
    active = fields.Boolean(default=True, help='Uncheck to archive the student record.')

    email = fields.Char(string='Email', required=True, help='Student email address.')
    phone = fields.Integer(string='Phone', help='Student contact number.')

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

    @api.depends('dob')
    def _compute_age(self):
        """Compute age from date of birth and validate minimum age."""
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
        """Replace temporary reference with admission number on registration"""
        for rec in self:
            if rec.reference_no and not rec.admission_no:
                rec.admission_no = self.env['ir.sequence'].next_by_code('education_student_admission')
                rec.reference_no = False
                rec.state = 'applied'

