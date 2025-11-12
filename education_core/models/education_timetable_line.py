# -*- coding: utf-8 -*-
from odoo import models, fields ,api
from odoo.exceptions import ValidationError

class EducationTimetableLine(models.Model):
    _name = 'education.timetable.line'
    _description = 'Education Timetable Line'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'display_name'


    subject_id = fields.Many2one('education.course', required=True)
    faculty_id = fields.Many2one('hr.employee', required=True, domain=[('role', '=', 'teacher')])
    day = fields.Selection([('monday','Monday'),('tuesday','Tuesday'),('wednesday','Wednesday'),('thursday','Thursday'),('friday','Friday')])
    start_time = fields.Float(required=True)
    end_time = fields.Float(required=True)
    room_id = fields.Many2one('education.class.room',help='Select the specific classroom or lab assigned to this class.'
    )
    class_id =fields.Many2one('education.class',string='Class')
    display_name = fields.Char(string="Display Name", compute="_compute_display_name", store=True)

    @api.depends('subject_id', 'faculty_id', 'day')
    def _compute_display_name(self):
        """Set display name as 'Subject - Teacher - Day'."""
        for rec in self:
            subject = rec.subject_id.name or ''
            teacher = rec.faculty_id.name or ''
            day = rec.day.capitalize() if rec.day else ''
            rec.display_name = f"{subject} - {teacher} - {day}" if subject and teacher and day else \
                f"{subject} - {teacher}" if subject and teacher else \
                    subject or teacher or day

    @api.constrains('room_id', 'start_time', 'end_time', 'day')
    def _check_room_availability(self):
        for rec in self:
            conflict = self.search([
                ('id', '!=', rec.id),
                ('room_id', '=', rec.room_id.id),
                ('day', '=', rec.day),
                ('start_time', '<', rec.end_time),
                ('end_time', '>', rec.start_time)
            ], limit=1)
            if conflict:
                raise ValidationError(f"Room {rec.room_id.name} already booked for this time slot.")


    @api.constrains('start_time', 'end_time')
    def _check_time_order(self):
        """Validate that start time is earlier than end time."""
        for rec in self:
            if rec.start_time >= rec.end_time:
                raise ValidationError("Start time must be earlier than end time.")


