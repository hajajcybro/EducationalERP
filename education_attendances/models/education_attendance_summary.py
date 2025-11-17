# -*- coding: utf-8 -*-
from odoo import models, fields, api

class EducationAttendanceSummary(models.Model):
    _name = 'education.attendance.summary'
    _description = 'Attendance Summary'
    _rec_name = 'student_id'

    student_id = fields.Many2one(
        'education.enrollment',
        string="Student",
        required=True,
    )

    program_id = fields.Many2one(
        'education.program',
        related='student_id.program_id',
        store=True,
        readonly=True
    )

    class_id = fields.Many2one(
        'education.class',
        related='student_id.current_class_id',
        store=True,
        readonly=True
    )
    academic_year_id = fields.Many2one(
        'education.academic.year',
        related='student_id.academic_year_id',
        store=True,)

    total_present = fields.Integer(default=0)
    total_absent = fields.Integer(default=0)
    total_excused = fields.Integer(default=0)

    attendance_percentage = fields.Float(
        compute="_compute_percentage",
        store=True,
        string="Attendance %"
    )

    @api.depends('total_present', 'total_absent', 'total_excused')
    def _compute_percentage(self):
        for rec in self:
            total_days = rec.total_present + rec.total_absent + rec.total_excused
            if total_days > 0:
                rec.attendance_percentage = (rec.total_present / total_days) * 100
            else:
                rec.attendance_percentage = 0.0


