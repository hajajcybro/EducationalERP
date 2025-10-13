# -*- coding: utf-8 -*-
from odoo import models, fields


class EducationEnrollment(models.Model):
    _name = 'education.enrollment'
    _description = 'Student Enrollment'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'student_id'
    _order = 'enrollment_date desc'

    student_id = fields.Char(string='Student', required=True)
    program_id = fields.Char(string='Program')
    class_id = fields.Char(string='Class')
    section = fields.Char(string='Section')
    batch_id = fields.Char(string='Batch')
    enrollment_date = fields.Date(string='Enrollment Date', default=fields.Date.context_today)
    start_date = fields.Date(string='Start Date')
    end_date = fields.Date(string='End Date')
    status = fields.Selection(
        [('enrolled', 'Enrolled'), ('promoted', 'Promoted'), ('retained', 'Retained'), ('dropped', 'Dropped'),
         ('completed', 'Completed')], string='Status', tracking=True)
    fee_plan_id = fields.Char(string='Fee Plan')
    roll_number = fields.Char(string='Roll Number')
    remarks = fields.Text(string='Remarks')
    student_image = fields.Image(string='Student Image', max_width=256, max_height=256)

    _sql_constraints = [
        ('unique_enrollment', 'unique(student_id, program_id, class_id, start_date)',
         'A student cannot be enrolled multiple times in the same program and class with the same start date.')
    ]
