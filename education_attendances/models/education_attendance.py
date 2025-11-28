# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import datetime


class EducationAttendance(models.Model):
    _name = 'education.attendance'
    _description = 'Education Attendance'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'class_id'


    class_id = fields.Many2one(
        'education.class', string="Class",
        required=True, tracking=True,
        help="Select the class for which attendance is being marked."
    )
    program_id = fields.Many2one(
        'education.program',
        related='class_id.program_id',
        store=True,
        readonly=True
    )
    timetable_line_id = fields.Many2one(
        'education.timetable.line',
        string="Timetable Slot",
        help="Choose the subject and period as per the timetable."
    )
    date = fields.Date(string="Date", required=True, default=fields.Date.context_today)
    faculty_id = fields.Many2one('hr.employee', string="Marked By",domain=[('role', '=', 'teacher')])
    attendance_line_ids = fields.One2many('education.attendance.line', 'attendance_id')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('marking','Marking'),
        ('submitted', 'Submitted'),
        ('validated', 'Validated')
    ], default='draft', string="Status", tracking=True)
    timetable_ids = fields.One2many('education.timetable.line','class_id')
    weekday = fields.Selection([
        ('monday', 'Monday'),
        ('tuesday', 'Tuesday'),
        ('wednesday', 'Wednesday'),
        ('thursday', 'Thursday'),
        ('friday', 'Friday'),
    ], compute='_compute_weekday', store=False, string='Day')

    _sql_constraints = [
        ('unique_student_class',
         'unique(student_id, class_id)',
         'Student is already enrolled in this class.')
    ]

    def action_submit(self):
        for rec in self:
            if not rec.attendance_line_ids:
                raise ValidationError(_("Please mark attendance for at least one student."))
            rec.state = 'submitted'

    def action_validate(self):
        """Admin validates attendance and triggers summary updates."""
        for rec in self:
            rec.state = 'validated'
            # rec._update_attendance_summary()
    # def _update_attendance_summary(self):
    #     """Update or create attendance summary for each student."""
    #     self.ensure_one()
    #     for line in self.attendance_line_ids:
    #         # Search for existing summary
    #         summary = self.env['education.attendance.summary'].search([
    #             ('student_id', '=', line.student_id.id),
    #         ], limit=1)
    #         if not summary:
    #             summary = self.env['education.attendance.summary'].create({
    #                 'student_id': line.student_id.id,
    #                 'total_present': 0,
    #                 'total_absent': 0,
    #                 'total_leave': 0,
    #             })
    #
    #             # Update counters based on status
    #         if line.status == 'present':
    #             summary.total_present += 1
    #         elif line.status == 'absent':
    #             summary.total_absent += 1
    #         elif line.status == 'leave':
    #             summary.total_leave += 1
    #         elif line.status == 'late':
    #             # If you want to count 'late' as present
    #             summary.total_present += 1

    def action_load_students(self):
        self.ensure_one()
        # get students correctly from res.partner
        students = self.class_id.student_ids.filtered(lambda s: s.position_role == 'student')

        Leave = self.env['education.leave.request']
        for student in students:
            leave = Leave.search([
                ('student_id', '=', student.id),
                ('status', '=', 'approved'),
                ('start_date', '<=', self.date),
                ('end_date', '>=', self.date),
            ], limit=1)
            status = 'present'
            remarks = ''
            if leave:
                if leave.leave_format == 'full_day':
                    status = 'leave'
                    remarks = 'Approved Full-Day Leave'
                elif leave.leave_format == 'half_day':
                    # ❗ Option A — Mark as 'leave'
                    status = 'leave'
                    remarks = 'Approved Half-Day Leave'

            self.env['education.attendance.line'].create({
                'attendance_id': self.id,
                'student_id': student.id,
                'status': status,
                'remarks': remarks,
            })
            self.state = 'marking'

    @api.depends()
    def _compute_weekday(self):
        for rec in self:
            # Use attendance date (NOT system date)
            if rec.date:
                rec.weekday = rec.date.strftime('%A').lower()
            else:
                rec.weekday = datetime.datetime.today().strftime('%A').lower()

