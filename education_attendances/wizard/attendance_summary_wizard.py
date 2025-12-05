# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError
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

    @api.constrains('date_from','date_to')
    def validation_constraints(self):
        """ Ensure `date_to` is not earlier than `date_from`."""
        for rec in self:
            if rec.date_from and rec.date_to:
                if rec.date_to < rec.date_from:
                    raise ValidationError("End date cannot be earlier than start date.")

    def action_open_summary(self):
        AttendanceLine = self.env['education.attendance.line']
        self.env['education.attendance.summary'].search([]).unlink()
        domain = []
        today = fields.Date.today()

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
            domain.append(('attendance_id.date', '=', today))

        elif self.summary_type == 'weekly':
            start_of_week = today - timedelta(days=today.weekday())
            end_of_week = start_of_week + timedelta(days=6)
            domain.append(('attendance_id.date', '>=', start_of_week))
            domain.append(('attendance_id.date', '<=', end_of_week))

        elif self.summary_type == 'monthly':
            first_day = today.replace(day=1)
            last_day = today.replace(day=calendar.monthrange(today.year, today.month)[1])
            domain.append(('attendance_id.date', '>=', first_day))
            domain.append(('attendance_id.date', '<=', last_day))

        elif self.summary_type == 'annual':
            first_day = today.replace(month=1, day=1)
            last_day = today.replace(month=12, day=calendar.monthrange(today.year, 12)[1])
            domain.append(('attendance_id.date', '>=', first_day))
            domain.append(('attendance_id.date', '<=', last_day))

        elif self.summary_type == 'custom':
            if self.date_from and not self.date_to:
                print('date from')
                domain.append(('attendance_id.date', '>=', self.date_from))
                domain.append(('attendance_id.date', '<=', today))
                # Case 2: Only date_to provided → exact date filter
            elif self.date_to and not self.date_from:
                domain.append(('attendance_id.date', '=', self.date_to))
                print('date to')

                # Case 3: Both provided
            elif self.date_from and self.date_to:
                print('bth')
                domain.append(('attendance_id.date', '>=', self.date_from))
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
                    'date_from': self.date_from or False,
                    'date_to' : self.date_to or False,
                    'total_present': 0,
                    'total_absent': 0,
                    'total_leave': 0,
                    'total_late': 0,
                }
            status = (line.status or '')
            if status in status_map:
                summary[studentid][status_map[status]] += 1
        to_create = self._compute_attendance_percentage(summary,lines)
        if to_create:
            self.env['education.attendance.summary'].create(to_create)
        return {
            'type': 'ir.actions.act_window',
            'name': "Attendance Summary",
            'res_model': 'education.attendance.summary',
            'view_mode': 'list,form',
            'target': 'current',
        }

    def _compute_attendance_percentage(self, summary,lines):
        """Compute attendance % for each student and return updated list."""
        # to_create = []
        # for vals in summary.values():
        #     present = vals['total_present'] + vals['total_late']
        #     leave = vals['total_leave']
        #     absent = vals['total_absent']
        #     total = present + leave + absent
        #     vals['attendance_percentage'] = (present / total * 100.0) if total else 0.0
        #     to_create.append(vals)
        # return to_create
        tracking_mode = self.env['ir.config_parameter'].sudo().get_param(
            'education_attendances.tracking_mode')
        print('tracking_mode',tracking_mode)
        to_create = []
        # Group lines by student + date
        daily_map = {}
        for line in lines:
            print(line)
            key = (
                line.student_id.id,
                line.attendance_id.class_id.id,
                line.attendance_id.date,
            )
            daily_map[key] = True  # just mark presence for that day

        for vals in summary.values():
            student_id = vals['student_id']
            class_id = vals['class_id']
            print(student_id,class_id)
            #DAY-WISE CALCULATION
            if tracking_mode == "day":

                present_days = 0
                absent_days = 0
                leave_days = 0

                # Loop through UNIQUE (student, class, date)
                for (sid, cls, dt) in daily_map.keys():

                    # Ensure only THIS student's class is counted
                    if sid != student_id or cls != class_id:
                        continue

                    # Collect statuses for this student/class/date
                    day_statuses = [
                        l.status.lower()
                        for l in lines
                        if l.student_id.id == sid
                           and l.attendance_id.class_id.id == cls
                           and l.attendance_id.date == dt
                    ]
                    # Apply rules
                    if "present" in day_statuses or "late" in day_statuses:
                        present_days += 1

                    elif all(s == "leave" for s in day_statuses):
                        leave_days += 1

                    elif "leave" in day_statuses and "present" not in day_statuses:
                        present_days += 0.5
                        absent_days += 0.5

                    elif all(s == "absent" for s in day_statuses):
                        absent_days += 1
                    else:
                        absent_days += 1

                total_days = present_days + absent_days + leave_days
                percentage = (present_days / total_days * 100) if total_days else 0


            #PERIOD-WISE CALCULATION (DEFAULT)
            else:
                present = vals['total_present'] + vals['total_late']
                leave = vals['total_leave']
                absent = vals['total_absent']
                total = present + leave + absent
                percentage = (present / total * 100) if total else 0
            vals['attendance_percentage'] = round(percentage, 2)
            to_create.append(vals)
        return to_create



