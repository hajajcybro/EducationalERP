# -*- coding: utf-8 -*-
from odoo import models, fields,api
from odoo.exceptions import ValidationError

class EducationTimetableSlot(models.Model):
    _name = 'education.timetable.slot'
    _description = 'Education Timetable Slot'

    template_id = fields.Many2one('education.timetable.template')
    date = fields.Date()
    line_id = fields.Many2one('education.timetable.line', required=True)
    class_id = fields.Many2one('education.class', required=True)
    subject_id = fields.Many2one('education.course', required=True)
    faculty_id = fields.Many2one('hr.employee', required=True)
    room_id = fields.Many2one('education.class.room')
    start_time = fields.Float()
    end_time = fields.Float()
    status = fields.Selection([
        ('scheduled', 'Scheduled'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled')
    ], default='scheduled')

    @api.constrains('start_time', 'end_time')
    def _check_time_order(self):
        """Validate that start time is earlier than end time."""
        for rec in self:
            if rec.start_time >= rec.end_time:
                raise ValidationError("Start time must be earlier than end time.")



