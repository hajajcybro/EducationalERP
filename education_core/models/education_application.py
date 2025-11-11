# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from datetime import date
import re





class EducationApplication(models.Model):
    _name = 'education.application'
    _description = 'Education Application'
    _inherit = ['mail.thread', 'mail.activity.mixin']
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
        string='Date of Birth', required=True, store=True,
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
    category_id = fields.Many2one('education.category',
        string='Category',
        help='Assign a category to the student.'
    )
    current_enrollment_id = fields.Many2one('education.enrollment',
        string='Current Enrollment',
        readonly=True,
        help='Link to the current enrollment record of the student.'
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

    guardian = fields.Char(
        string='Guardians',
        help='Enter the student’s guardians or parents.'
    )
    id_no = fields.Char('Aadhar No. / ID No.', help='Government-issued ID number')
    relation = fields.Char(string='Relation',  help="Relationship of the guardian to the applicant" )
    father_name = fields.Char('Father Name')
    mother_name = fields.Char('Mother Name')
    contact_no = fields.Char('Contact Number')
    emergency_phone = fields.Char('Emergency Phone Number')

    contact_address = fields.Text('Permanent Address')
    occupation = fields.Char('Occupation',help='Job or business')

    previous_academic = fields.Char('Previous Academic')
    previous_class = fields.Char('Previous Class')
    Year_of_passing = fields.Char('Year Of Passing')
    language = fields.Char('Language / Medium')
    board = fields.Char('Board / University')


    @api.depends('dob')
    def _compute_age(self):
        """Compute age from date of birth."""
        for record in self:
            if record.dob:
                record.age = int((date.today() - record.dob).days / 365.25)  # More accurate
            else:
                record.age = 0

    @api.constrains('dob')
    def _check_age_minimum(self):
        """Validate minimum age requirement."""
        for record in self:
            if record.dob:
                age = (date.today() - record.dob).days / 365.25
                if age < 5:
                    raise ValidationError(_('Student must be at least 5 years old. Current age: %.1f years') % age)
                if age > 100:
                    raise ValidationError(_('Please enter a valid date of birth.'))

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
                    'stu_category_id': rec.category_id,
                    'guardian': rec.guardian,
                    'id_no' : rec.id_no,
                    'relation' : rec.relation,
                    'father_name' : rec.father_name,
                    'mother_name' : rec.mother_name,
                    'contact_no' : rec.contact_no,
                    'emergency_phone' : rec.emergency_phone,
                    'current_address' : rec.contact_address,
                    'previous_academic' : rec.previous_academic,
                    'previous_class': rec.previous_class,
                    'Year_of_passing': rec.Year_of_passing,
                    'language': rec.language,
                    'board': rec.board,
                })

    @api.constrains('email', 'phone', 'contact_no', 'emergency_phone')
    def _check_contact_fields(self):
        """Validate email and phone formats."""
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        phone_pattern = r'^\+?\d{7,15}$'

        for record in self:
            if record.email and not re.match(email_pattern, record.email):
                raise ValidationError(_('Invalid email address. Please enter a valid format like name@example.com.'))

            phone_fields = {
                'Phone': record.phone,
                'Contact Number': record.contact_no,
                'Emergency Phone': record.emergency_phone,
            }
            for field_label, value in phone_fields.items():
                if value and not re.match(phone_pattern, value):
                    raise ValidationError(_(
                        'Invalid %s. Please enter digits only (7–15 numbers) with optional + sign.'
                    ) % field_label)

    @api.constrains('program_id', 'academic_year_id')
    def _check_duration_match(self):
        """Ensure program duration matches academic year duration."""
        for rec in self:
            if rec.program_id and rec.academic_year_id:
                program_duration = rec.program_id.duration or 0.0
                year_duration = rec.academic_year_id.duration or 0.0
                if float(program_duration) != float(year_duration):
                    raise ValidationError(_(
                        "Duration mismatch: The selected program (%s years) "
                        "does not match the academic year (%s years)."
                    ) % (program_duration, year_duration))

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

    def action_to_review(self):
            """Cancel the leave request."""
            for rec in self:
                rec.state = 'to_review'

    def action_verified(self):
            """Cancel the leave request."""
            for rec in self:
                rec.state = 'verified'





