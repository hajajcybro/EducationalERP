# -*- coding: utf-8 -*-
from odoo import models, fields

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
    admission_no = fields.Char(string='Admission Number')
    class_id = fields.Many2one('education.class', string='Class')
    current_enrollment_id = fields.Many2one('education.enrollment',
                                            string='Current Enrollment',
                                            readonly=True,
                                            help='Link to the current enrollment record of the student.'
                                            )
    roll_no = fields.Char('Roll Number')
    class_teacher_id = fields.Many2one('res.partner', string='Class Teacher',
                                       domain=[('position_role', '=', 'teacher')])
    scholarship_id = fields.Many2one('education.scholarship',string='Scholarship')


    #personal info
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
    category = fields.Many2one('education.category',
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
