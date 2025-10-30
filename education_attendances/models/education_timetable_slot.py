# -*- coding: utf-8 -*-
from odoo import models, fields,api
from odoo.exceptions import ValidationError

class EducationTimetableSlot(models.Model):
    _name = 'education.timetable.slot'
    _description = 'Education Timetable Slot'
    _order = 'date asc'

    template_id = fields.Many2one('education.timetable',string='Slot')
    date = fields.Date()
    day = fields.Selection([
        ('monday', 'Monday'),
        ('tuesday', 'Tuesday'),
        ('wednesday', 'Wednesday'),
        ('thursday', 'Thursday'),
        ('friday', 'Friday'),
        ('saturday', 'Saturday'),
        ('sunday', 'Sunday'),
    ], string='Day', compute='_compute_day', store=True)

    faculty_id = fields.Many2one('hr.employee')
    start_time = fields.Float()
    class_id = fields.Many2one('education.class', string='Class')
    end_time = fields.Float()
    status = fields.Selection([
        ('scheduled', 'Scheduled'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled')
    ], default='scheduled')

    attendance_line_ids = fields.One2many(
        'education.attendance',
        'student_id',
        string='Attendance Lines',
        compute='_compute_attendance_lines',
        store=False
    )

    @api.depends('class_id', 'template_id')
    def _compute_attendance_lines(self):
        """Auto-load students of the slot's class."""
        student = self.env['res.partner']
        for slot in self:
            # Remove any existing temporary records
            slot.attendance_line_ids = [(5, 0, 0)]
            # Determine the class — from slot or template
            class_rec = slot.class_id or slot.template_id.class_id
            if class_rec:
                students = student.search([('class_id', '=', class_rec.id)])
                slot.attendance_line_ids = [
                    (0, 0, {
                        'student_id': stu.id,
                        'roll_no': stu.roll_no,
                        'present': True,
                    }) for stu in students
                ]



    @api.constrains('start_time', 'end_time')
    def _check_time_order(self):
        """Validate that start time is earlier than end time."""
        for rec in self:
            if rec.start_time >= rec.end_time:
                raise ValidationError("Start time must be earlier than end time.")

    @api.depends('date')
    def _compute_day(self):
        """Compute the weekday name from the date."""
        for rec in self:
            rec.day = rec.date.strftime('%A').lower() if rec.date else False

    def action_done(self):
        for rec in self:
            rec.status = 'completed'
