# -*- coding: utf-8 -*-
from odoo import models, fields, api
from datetime import date

class EducationAttendanceSummary(models.TransientModel):
    _name = 'education.attendance.summary'
    _description = 'Education Attendance Summary'


    # Academic structure
    academic_year_id = fields.Many2one('education.academic.year', string="Academic Year", readonly=True)
    program_id       = fields.Many2one('education.program', string="Program", readonly=True)
    class_id         = fields.Many2one('education.class', string="Class", readonly=True)
    subject_id       = fields.Many2one('education.course', string="Subject", readonly=True)

    student_id = fields.Many2one('res.partner', string='Student', readonly=True,
                                 domain = [('position_role','=',' student')])

    # Summary type
    summary_type = fields.Selection([
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('annual', 'Annual'),
        ('subject', 'Subject-wise'),
        ('custom', 'Custom Range'),
    ], string='Summary Type', readonly=True)

    date = fields.Date( string='Date', readonly=True,
        default=lambda self: fields.Date.today()
    )
    month = fields.Integer(
        string='Month', readonly=True,
        default=lambda self: date.today().month
    )
    year = fields.Char(
        string='Year', readonly=True,
        default=lambda self: date.today().year
    )

    # Attendance counts
    total_present = fields.Integer(string='Present', readonly=True)
    total_absent  = fields.Integer(string='Absent', readonly=True)
    total_leave   = fields.Integer(string='Leave', readonly=True)
    total_late    = fields.Integer(string='Late', readonly=True)

    attendance_percentage = fields.Float(string='Attendance %', readonly=True)
