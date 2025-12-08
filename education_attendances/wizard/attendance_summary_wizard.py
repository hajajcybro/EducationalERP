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
        tracking_mode = self.env['ir.config_parameter'].sudo().get_param(
            'education_attendances.tracking_mode')
        to_create = []
        for vals in summary.values():
            student_id = vals['student_id']
            class_id = vals['class_id']

            student_lines = [
                l for l in lines
                if l.student_id.id == student_id
                and l.attendance_id.class_id.id == class_id
            ]

            if tracking_mode == "day":
                print('day')
                daily_status = {}
                for line in student_lines:
                    date = line.attendance_id.date
                    if date not in daily_status:
                        daily_status[date] = set()

                    if line.status:
                        daily_status[date].add(line.status.lower())
                present_days = 0
                absent_days = 0
                leave_days = 0
                late_days = 0

                for date, statuses in daily_status.items():
                    if "present" in statuses or "late" in statuses:
                        present_days += 1
                    elif statuses == {"leave"}:
                        leave_days += 1
                    elif "leave" in statuses and "absent" in statuses:
                        # Mix of leave and absent on same day
                        leave_days += 0.5
                        absent_days += 0.5
                    elif "absent" in statuses:
                        absent_days += 1
                    else:
                        absent_days += 1

                # Update vals to show DAYS not periods
                vals['total_present'] = int(present_days)
                vals['total_absent'] = int(absent_days)
                vals['total_leave'] = int(leave_days)
                vals['total_late'] = 0  # Included in present_days

                total_days = present_days + absent_days + leave_days
                percentage = (present_days / total_days * 100) if total_days else 0

            elif tracking_mode == "period":
                print('period')
                # Use the already-calculated period counts from summary
                present = vals['total_present'] + vals['total_late']
                leave = vals['total_leave']
                absent = vals['total_absent']
                total = present + leave + absent
                percentage = (present / total * 100) if total else 0

            elif tracking_mode == "session_wise":
                print('session')
                session_status = {}
                for line in student_lines:
                    date = line.attendance_id.date
                    period_time = line.attendance_id.timetable_line_id.start_time if hasattr(line.attendance_id,
                                                                                             'timetable_line_id') and line.attendance_id.timetable_line_id else None
                    session = "afternoon" if (period_time and period_time >= 12.0) else "morning"
                    key = (date, session)
                    if key not in session_status:
                        session_status[key] = set()
                    if line.status:
                        session_status[key].add(line.status.lower())

                present_sessions = absent_sessions = leave_sessions = 0

                for statuses in session_status.values():
                    if "present" in statuses or "late" in statuses:
                        present_sessions += 1
                    elif statuses == {"leave"}:
                        leave_sessions += 1
                    elif "leave" in statuses and "absent" in statuses:
                        leave_sessions += 0.5
                        absent_sessions += 0.5
                    else:
                        absent_sessions += 1

                vals.update({
                    'total_present': int(present_sessions),
                    'total_absent': int(absent_sessions),
                    'total_leave': int(leave_sessions),
                    'total_late': 0
                })

                total_sessions = present_sessions + absent_sessions + leave_sessions
                percentage = (present_sessions / total_sessions * 100) if total_sessions else 0

            if tracking_mode == "hourly":
                print("Hourly mode applied")
                course = self.env['education.course'].browse(vals.get('subject_id'))
                if course and course.course_type == 'credit_hour':
                    total_hours = 0
                    for l in student_lines:
                        duration = l.attendance_id.timetable_line_id.duration or 0
                        if l.status in ['present', 'late']:
                            total_hours += duration

                    required_hours = course.credit_hours
                    vals['total_hours_attended'] = total_hours
                    vals['required_credit_hours'] = required_hours
                    if required_hours > 0:
                        percentage = (total_hours / required_hours) * 100
                    else:
                        percentage = 0
                    vals['attendance_percentage'] = round(percentage, 2)
                    to_create.append(vals)
                    continue
            else:
                percentage = 0
            vals['attendance_percentage'] = round(percentage, 2)
            to_create.append(vals)
        return to_create
