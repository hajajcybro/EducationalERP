# -*- coding: utf-8 -*-
from odoo import models, fields, api

class AttendanceSummaryWizard(models.TransientModel):
    _name = 'attendance.summary.wizard'
    _description = 'Attendance Summary'

    summary_type = fields.Selection([
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('annual', 'Annual'),
        ('subject', 'Subject-wise'),
        ('custom', 'Custom Range'),
    ], default='monthly', string="Summary Type", required=True)
    date_from = fields.Date(string="From")
    date_to = fields.Date(string="To")

    academic_year_id = fields.Many2one('education.academic.year', string="Academic Year")
    program_id = fields.Many2one('education.program', string="Program")
    class_id = fields.Many2one('education.class', string="Class")
    subject_id = fields.Many2one('education.course', string="Subject")

    def action_open_summary(self):
        # Load config
        mode = self.env['ir.config_parameter'].sudo().get_param(
            'education_attendances.attendance_tracking_mode'
        )
        if not mode:
            mode = 'day'

        AttendanceLine = self.env['education.attendance.line']
        Summary = self.env['education.attendance.summary']
        Summary.search([]).unlink()
        domain = []

        if self.academic_year_id:
            domain.append(('attendance_id.clas_id.academic_year_id', '=', self.academic_year_id.id))
            print(domain)

        if self.program_id:
            domain.append(('attendance_id.program_id', '=', self.program_id.id))
            print(domain)

        if self.class_id:
            domain.append(('attendance_id.class_id', '=', self.class_id.id))
            print(domain)

        if self.subject_id:
            domain.append(('subject_id', '=', self.subject_id.id))
            print(domain)

        if self.summary_type == 'custom':
            if self.date_from:
                domain.append(('attendance_id.date', '>=', self.date_from))
            if self.date_to:
                domain.append(('attendance_id.date', '<=', self.date_to))

        lines = AttendanceLine.search(domain)
        print('line',lines.read())
        if domain:
            lines = AttendanceLine.search(domain + [('attendance_id.state', '=', 'validated')])
        else:
            lines = AttendanceLine.search([('attendance_id.state', '=', 'validated')])

        status_map = {
            'present': 'total_present',
            'absent': 'total_absent',
            'leave': 'total_leave',
            'late': 'total_late',
        }
        summary = {}

        for line in lines:
            sid = line.student_id.id
            if sid not in summary:
                summary[sid] = {
                    'academic_year_id': line.attendance_id.class_id.academic_year_id.id if line.attendance_id.class_id else False,
                    'program_id': line.attendance_id.program_id.id if line.attendance_id.program_id else False,
                    'class_id': line.attendance_id.class_id.id if line.attendance_id.class_id else False,
                    'student_id': sid,
                    'summary_type': self.summary_type,

                    'date': self.date_from,
                    'month': self.date_from.month if self.date_from else False,
                    'year': self.date_from.year if self.date_from else False,

                    'total_present': 0,
                    'total_absent': 0,
                    'total_leave': 0,
                    'total_late': 0,
                }
            stu = (line.status or '').lower()
            if stu in status_map:
                summary[sid][status_map[stu]] += 1

        # Create summary records and compute percentage
        to_create = []
        for vals in summary.values():
            present = vals['total_present'] + vals['total_late']
            leave = vals['total_leave']
            absent = vals['total_absent']
            denom = present + leave + absent
            vals['attendance_percentage'] = (present / denom * 100.0) if denom else 0.0
            to_create.append(vals)

        if to_create:
            Summary.create(to_create)

        return {
            'type': 'ir.actions.act_window',
            'name': "Attendance Summary",
            'res_model': 'education.attendance.summary',
            'view_mode': 'list,form',
            'target': 'current',
        }





