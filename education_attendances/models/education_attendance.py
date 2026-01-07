# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

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

    def action_submit(self):
        for rec in self:
            rec.state = 'submitted'

    def action_validate(self):
        """Admin validates attendance and triggers summary updates."""
        for rec in self:
            rec.state = 'validated'

    def action_load_students(self):
        """ Load all students of the selected class and mark their attendance.
        Each student is marked as present by default. If the student has an
        approved leave for the selected date, the attendance is marked as
        leave. Attendance lines are created and the record is moved to the
        marking state."""
        self.ensure_one()
        students = self.class_id.student_ids

        for student in students:
            leave = self.env['education.leave.request'].search([
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
                    status = 'leave'
                    remarks = 'Approved Half-Day Leave'
            self.env['education.attendance.line'].create({
                'attendance_id': self.id,
                'student_id': student.id,
                'status': status,
                'remarks': remarks,
            })
            self.state = 'marking'

    @api.depends('date')
    def _compute_weekday(self):
        """Compute the day based on the attendance date.
        The day is derived from the `date` field and stored in lowercase to
        align with the model's day selection values. This ensures consistent
        behavior when filtering or matching timetable records."""
        for rec in self:
            rec.weekday = rec.date.strftime('%A').lower() if rec.date else False

    @api.model
    def attendance_mail_notify(self):
        """Check overall attendance %, notify parents if below minimum."""
        params = self.env['ir.config_parameter'].sudo()
        today = fields.Date.today()
        if params.get_param('education_attendances.attendance_enabled') == "True":
            print('true')
            minimum = float(
                params.get_param('education_attendances.minimum_attendance') or 0
            )
            frequency = params.get_param(
                'education_attendances.notify_frequency', 'monthly'
            )
            attendances = self.search([
                ('state', '=', 'validated'),
                ('class_id.academic_year_id.state', '=', 'closed'),
                ('class_id.session_id.state', '=', 'closed'),
            ]).mapped('attendance_line_ids')
            print('attendances---',attendances)
            for student in attendances.mapped('student_id'):
                print('stud',student)
                student_lines = attendances.filtered(
                    lambda l: l.student_id == student
                )
                print('hhhhhhhhh',student_lines)
                total = len(student_lines)
                present = len(student_lines.filtered(
                    lambda l: l.status == 'present'
                ))
                print(present)
                percentage = (present / total * 100) if total else 0
                print(percentage)
                send_mail = True
                last = student.last_attendance_mail_date
                print(last)
                if last:
                    if frequency == 'daily' and last == today:
                        send_mail = False
                    elif frequency == 'weekly' and last.isocalendar()[1] == today.isocalendar()[1]:
                        send_mail = False
                    elif frequency == 'monthly' and last.month == today.month and last.year == today.year:
                        send_mail = False
                    elif frequency == 'yearly' and last.year == today.year:
                        send_mail = False
                if send_mail and student.parent_email and percentage < minimum:
                    print('minimum')
                    self.env['mail.mail'].sudo().create({
                        'subject': 'Attendance Warning',
                        'body_html': (
                            f"Attendance for <b>{student.name}</b>: "
                            f"{percentage:.2f}% (Minimum Required: {minimum}%)"
                        ),
                        'email_to': student.parent_email,
                        'auto_delete': True,
                    }).send()
                    student.last_attendance_mail_date = today

    # @api.model
    # def attendance_mail_notify(self):
    #     """Check overall attendance %, notify parents if below minimum."""
        # params = self.env['ir.config_parameter'].sudo()
        # today = fields.Date.today()
        # if params.get_param('education_attendances.attendance_enabled') == "True":
        #     minimum = float(params.get_param('education_attendances.minimum_attendance') or 0)
        #     lines = self.searchself.search([
        #                     ('state', '=', 'validated'),
        #                     ('class_id.academic_year_id.state', '=', 'closed'),
        #                     ('class_id.session_id.state', '=', 'closed'),
        #                 ]).mapped('attendance_line_ids')
        #     for student in lines.mapped('student_id'):
        #         student_lines = lines.filtered(lambda l: l.student_id == student)
        #         total = len(student_lines)
        #         present = len(student_lines.filtered(lambda l: l.status == 'present'))
        #         percentage = (present / total * 100) if total else 0
        #         # Send email only if parent email exists and attendance is low
        #         if student.parent_email and percentage < minimum:
        #             self.env['mail.mail'].sudo().create({
        #                 'subject': 'Monthly Attendance Warning',
        #                 'body_html': (
        #                     f"Attendance for <b>{student.name}</b>: "
        #                     f"{percentage:.2f}% (Minimum {minimum}%)"
        #                 ),
        #                 'email_to': student.parent_email,
        #                 'auto_delete': True,
        #             }).send()
        #             student.last_attendance_mail_date = today