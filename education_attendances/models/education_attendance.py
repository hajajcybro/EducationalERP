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
    timetable_id = fields.Many2one(
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

    def action_submit(self):
        for rec in self:
            if not rec.attendance_line_ids:
                raise ValidationError(_("Please mark attendance for at least one student."))
            rec.state = 'submitted'

    def action_validate(self):
        """Admin validates attendance and triggers summary updates."""
        for rec in self:
            rec.state = 'validated'
            rec._update_summary()

    def action_load_students(self):
        """Auto-load students enrolled in this class into attendance lines."""
        for rec in self:
            if not rec.class_id:
                raise ValidationError(_("Select a class first."))
            enrollments = rec.class_id.student_ids
            lines = [(0, 0, {'student_id': s.id, 'status': 'present'}) for s in enrollments]
            rec.attendance_line_ids = lines
            rec.state = 'marking'

