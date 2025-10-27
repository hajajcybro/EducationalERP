# -*- coding: utf-8 -*-
from odoo import models, fields

class EducationTimetableSlot(models.Model):
    _name = 'education.timetable.slot'
    _description = 'Education Timetable Slot'
    _rec_name = 'display_name'

    class_id = fields.Many2one('education.class', string='Class', required=True)
    day = fields.Selection([
        ('monday', 'Monday'),
        ('tuesday', 'Tuesday'),
        ('wednesday', 'Wednesday'),
        ('thursday', 'Thursday'),
        ('friday', 'Friday'),
        ('saturday', 'Saturday'),
    ], string='Day', required=True)
    start_time = fields.Float(string='Start Time', required=True, help='Time in 24h format, e.g. 9.5 = 9:30 AM')
    end_time = fields.Float(string='End Time', required=True)
    subject_id = fields.Many2one('education.course', string='Subject / Course')
    faculty_id = fields.Many2one('hr.employee', string='Faculty', domain=[('role', '=', 'teacher')])
    room_id = fields.Many2one('education.class.room', string='Room')
    slot_type = fields.Selection([
        ('lecture', 'Lecture'),
        ('lab', 'Lab'),
        ('tutorial', 'Tutorial'),
    ], string='Slot Type', default='lecture')
    display_name = fields.Char(string='Display Name', compute='_compute_display_name', store=True)

    def _compute_display_name(self):
        for rec in self:
            rec.display_name = f"{rec.class_id.name or ''} - {rec.day.title()} ({rec.start_time} - {rec.end_time})"


