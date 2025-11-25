# -*- coding: utf-8 -*-
from odoo import models, fields, api

class ResPartner(models.Model):
    """Extend partner to add position role"""
    _inherit = 'res.partner'

    position_role = fields.Selection(
        selection=[('teacher', 'Teacher'), ('student', 'Student')],
        string='Position',
    )
    email = fields.Char(string='Email', required=True, help='Student email address.')
    phone = fields.Char(string='Phone', help='Student contact number.')
    academic_year_id = fields.Many2one('education.academic.year', string='Academic Year')
    program_id = fields.Many2one('education.program',string='Program', required=True)

    # Academic Info
    admission_no = fields.Char(string='Admission Number',)
    class_id = fields.Many2one('education.class', string='Class')
    current_enrollment_id = fields.Many2one('education.enrollment',
                                            string='Current Enrollment',
                                            readonly=True,
                                            help='Link to the current enrollment record of the student.'
                                            )
    roll_no = fields.Char('Roll Number')
    class_teacher_id = fields.Many2one('res.partner', string='Class Teacher',
                                       domain=[('position_role', '=', 'teacher')])

   #parent details
    father_name = fields.Char('Father Name')
    mother_name = fields.Char('Mother Name')
    contact_no = fields.Char('Contact Number')
    emergency_phone = fields.Char('Emergency Phone Number')
    current_address = fields.Text('Permanent Address')
    occupation = fields.Char('Occupation', help='Job or business')

    #personal info
    id_no = fields.Char('Aadhar No. / ID No.', help='Government-issued ID number')
    relation = fields.Char(string='Relation', help="Relationship of the guardian to the applicant")
    dob = fields.Date('Date of Birth')
    age = fields.Integer('Age')
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

    #previouse academic details
    previous_academic = fields.Char('Previous Academic')
    previous_class = fields.Char('Previous Class')
    Year_of_passing = fields.Char('Year Of Passing')
    language = fields.Char('Language / Medium')
    board = fields.Char('Board / University')


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

    @api.model
    def create(self, vals):
        """Override create to assign an admission number when a new student
        is added without one."""
        vals_list = vals if isinstance(vals, list) else [vals]

        for val in vals_list:
            if val.get('position_role') == 'student' and not val.get('admission_no'):
                val['admission_no'] = self.env['ir.sequence'].next_by_code('education_student_admission')

        return super().create(vals_list)

    def write(self, vals):
        """Override write to generate an admission number when a partner
        becomes a student and lacks one."""
        for rec in self:
            if vals.get('position_role') == 'student' and not rec.admission_no:
                vals['admission_no'] = self.env['ir.sequence'].next_by_code('education_student_admission')

        return super().write(vals)


