# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from datetime import date

class EducationApplication(models.Model):
    _name = 'education.application'
    _description = 'Education Application'
    _inherit = 'mail.thread'
    _order = 'admission_no'

    name = fields.Char('Student Name',
            required = True,
            help = 'Enter the full name of the student.'
    )
    program_id = fields.Many2one('education.program',string='Program', required=True)
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
        ('application', 'Application'),
        ('to_review','To Review'),
        ('verified','Verified'),
        ('admission', 'Admission'),
        ('enrolled', 'Enrolled'),
        ('rejected', 'Rejected'),
    ], string='Status', default='application',tracking=True, help='Current status of the student.'
    )

    reject_reason = fields.Text('Rejection Reason')
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
    academic_year_id = fields.Many2one('education.academic.year',string='Academic Year',
                                    domain=[('state', '!=', 'closed')],
                                    )
    partner_id = fields.Many2one('res.partner', string='Related Contact', readonly=True,
                                 help='Linked res.partner record for this student.')

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
                rec.state = 'admission'

            partner = rec.partner_id
            if not partner:
                partner = self.env['res.partner'].create({
                    'name': rec.name,
                    'email': rec.email,
                    'phone': rec.phone,
                    'street': rec.street,
                    'street2': rec.street2,
                    'city': rec.city,
                    'zip': rec.zip,
                    'country_id': rec.country_id.id,
                    'state_id': rec.state_id.id,
                    'position_role': 'student',

                })
            rec.partner_id = partner.id
            partner.write({
                    'admission_no': rec.admission_no,
                    'program_id': rec.program_id.id,
                    'academic_year_id': rec.academic_year_id.id,
                    'gender': rec.gender,
                    'dob': rec.dob,
                    'age': rec.age,
                    'blood_group': rec.blood_group,
                    'category': rec.category,
                    'guardian': rec.guardian,
                })

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
        default_class = self.env['education.class'].search([
            ('program_id', '=', self.program_id.id),
            ('academic_year_id', '=', self.academic_year_id.id),
        ], limit=1)
        return {
            'type': 'ir.actions.act_window',
            'name': 'Enroll Student',
            'res_model': 'education.enrollment',
            'view_mode': 'form',
            'target': 'current',
            'context': {
                'default_student_id': self.id,
                'default_status': 'enrolled',
                'default_current_class_id':default_class.id if default_class else False,
            },
        }


    def action_reject(self):
        """This opens a popup wizard to ask reject reason"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Reject Application',
            'res_model': 'education.application.reject.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_application_id': self.id},
        }


    @api.onchange('state')
    def _onchange_state_limit(self):
        for rec in self:
            # Allow only manual change among these 3
            allowed_manual = ['admission', 'enrolled','rejected']
            if rec.state in allowed_manual:
                raise ValidationError(_("You can't change state"))





