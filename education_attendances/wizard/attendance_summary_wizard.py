# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import AccessError, ValidationError
from datetime import timedelta
import calendar


class AttendanceSummaryWizard(models.TransientModel):
    _name = 'attendance.summary.wizard'
    _description = 'Attendance Summary'

    summary_type = fields.Selection([
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('annual', 'Annual'),
        ('custom', 'Custom Range'),
    ], default='monthly', string="Summary Type", required=True)
    date_from = fields.Date(string="From")
    date_to = fields.Date(string="To")
    academic_year_id = fields.Many2one('education.academic.year', string="Academic Year")
    program_id = fields.Many2one('education.program', string="Program")
    class_id = fields.Many2one('education.class', string="Class")
    subject_id = fields.Many2one('education.course', string="Subject")
    today = fields.Date.today()

    @api.constrains('program_id', 'academic_year_id')
    def _check_program_year_duration(self):
        """ Ensure the Academic Year duration matches the selected Program's duration.
        Raises a ValidationError if both durations are different."""
        for rec in self:
            if rec.program_id and rec.academic_year_id:
                if int(rec.academic_year_id.duration) != rec.program_id.duration:
                    raise ValidationError(
                        f"Academic year '{rec.academic_year_id.name}' (duration {rec.academic_year_id.duration}) "
                        f"does not match the duration of program '{rec.program_id.name}' ({rec.program_id.duration} years)."
                    )

    def action_open_summary(self):
        mode = self.env['ir.config_parameter'].sudo().get_param(
            'education_attendances.attendance_tracking_mode')

        AttendanceLine = self.env['education.attendance.line']
        Summary = self.env['education.attendance.summary'].search([]).unlink()
        domain = []

        if self.academic_year_id:
            domain.append(('attendance_id.class_id.academic_year_id', '=', self.academic_year_id.id))

        if self.program_id:
            domain.append(('attendance_id.program_id', '=', self.program_id.id))

        if self.class_id:
            domain.append(('attendance_id.class_id', '=', self.class_id.id))

        if self.subject_id:
            domain.append(('attendance_id.timetable_line_id.subject_id', '=', self.subject_id.id))

        # summary type filters
        if self.summary_type == 'daily':
            domain.append(('attendance_id.date', '=', fields.Date.today()))

        elif self.summary_type == 'weekly':
            start_of_week = self.today - timedelta(days=self.today.weekday())
            end_of_week = start_of_week + timedelta(days=6)
            domain.extend([
                ('attendance_id.date', '>=', start_of_week),
                ('attendance_id.date', '<=', end_of_week)
            ])

        elif self.summary_type == 'monthly':
            first_day = self.today.replace(day=1)
            last_day = self.today.replace(day=calendar.monthrange(self.today.year, self.today.month)[1])
            domain.append(('attendance_id.date', '>=', first_day))
            domain.append(('attendance_id.date', '<=', last_day))

        elif self.summary_type == 'annual':
            first_day = self.today.replace(month=1, day=1)
            last_day = self.today.replace(month=12, day=calendar.monthrange(self.today.year, 12)[1])
            domain.append(('attendance_id.date', '>=', first_day))
            domain.append(('attendance_id.date', '<=', last_day))

        elif self.summary_type == 'custom':
            if self.date_from:
                domain.append(('attendance_id.date', '>=', self.date_from))
            if self.date_to:
                domain.append(('attendance_id.date', '<=', self.date_to))

        domain.append(('attendance_id.state', '=', 'validated'))
        lines = AttendanceLine.search(domain)
        status_map = {
            'present': 'total_present',
            'absent': 'total_absent',
            'leave': 'total_leave',
            'late': 'total_late',
        }
        summary = {}

        for line in lines:
            studentid = line.student_id.id
            if studentid not in summary:
                summary[studentid] = {
                    'academic_year_id': line.attendance_id.class_id.academic_year_id.id or False,
                    'program_id': line.attendance_id.program_id.id or False,
                    'class_id': line.attendance_id.class_id.id or False,
                    'subject_id': line.attendance_id.timetable_line_id.subject_id.id or False,
                    'student_id': studentid,
                    'summary_type': self.summary_type,
                    'total_present': 0,
                    'total_absent': 0,
                    'total_leave': 0,
                    'total_late': 0,
                }
            status = (line.status or '')
            if status in status_map:
                summary[studentid][status_map[status]] += 1

        # Create summary records and compute percentage
        to_create = []
        for vals in summary.values():
            present = vals['total_present'] + vals['total_late']
            leave = vals['total_leave']
            absent = vals['total_absent']
            total = present + leave + absent
            vals['attendance_percentage'] = (present / total * 100.0) if total else 0.0
            to_create.append(vals)
        if to_create:
            self.env['education.attendance.summary'].create(to_create)

        return {
            'type': 'ir.actions.act_window',
            'name': "Attendance Summary",
            'res_model': 'education.attendance.summary',
            'view_mode': 'list,form',
            'target': 'current',
        }





