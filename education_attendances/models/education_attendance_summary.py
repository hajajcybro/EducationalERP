# -*- coding: utf-8 -*-
from odoo import models, fields, api

class EducationAttendanceSummary(models.Model):
    _name = 'education.attendance.summary'
    _description = 'Attendance Summary'
    _rec_name = 'student_id'

    student_id = fields.Many2one(
        'res.partner',domain=[('position_role','=','student')],
        string="Student",
        required=True,
    )
    summary_type = fields.Selection([
        ('daily', 'Daily'),
        ('monthly', 'Monthly'),
        ('annual', 'Annual'),
        ('subject', 'Subject-wise'),
        ('term', 'Term-wise'),
    ], required=True)

    date = fields.Date()
    month = fields.Char()
    year = fields.Char()

    subject_id = fields.Many2one('education.course')

    # Calculated values
    total_present = fields.Integer()
    total_absent = fields.Integer()
    total_leave = fields.Integer()

    attendance_percentage = fields.Float(
        compute="_compute_percentage",
        store=True
    )
    class_id = fields.Many2one(
        'education.class',
        related='student_id.class_id',
        store=True,
        readonly=True
    )
    _sql_constraints = [
        ('unique_summary',
         'unique(student_id, summary_type, date, month, year, subject_id, term_id)',
         'Summary record already exists!')
    ]

    @api.depends('total_present', 'total_absent', 'total_leave')
    def _compute_percentage(self):
            for rec in self:
                total = rec.total_present + rec.total_absent + rec.total_leave
                rec.attendance_percentage = (rec.total_present / total * 100) if total else 0.0
