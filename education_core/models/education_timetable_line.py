# -*- coding: utf-8 -*-
from odoo import models, fields ,api
from odoo.exceptions import ValidationError


class EducationTimetableLine(models.Model):
    _name = 'education.timetable.line'
    _description = 'Education Timetable Line'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'display_name'

    subject_id = fields.Many2one('education.subject', required=True)
    faculty_id = fields.Many2one('hr.employee', required=True, domain=[('role', '=', 'teacher')])
    day = fields.Selection([('monday','Monday'),('tuesday','Tuesday'),('wednesday','Wednesday'),('thursday','Thursday'),('friday','Friday')])
    start_time = fields.Float(required=True)
    end_time = fields.Float(required=True)
    room_id = fields.Many2one('education.class.room',help='Select the specific classroom or lab assigned to this class.'
    )
    class_id = fields.Many2one('education.class',string='Class')
    program_id = fields.Many2one(
        'education.program',
        related='class_id.program_id',
        store=True,
        readonly=True
    )
    display_name = fields.Char(string="Display Name", compute="_compute_display_name", store=True)
    duration = fields.Float('Duration', compute='_compute_duration', store=True)

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

    @api.constrains('start_time', 'end_time')
    def _check_time_order(self):
        """Validate that start time is earlier than end time."""
        for rec in self:
            if rec.start_time >= rec.end_time:
                raise ValidationError("Start time must be earlier than end time.")

    @api.depends('start_time', 'end_time')
    def _compute_duration(self):
        """Compute class duration in hours."""
        for rec in self:
            duration = 0.0
            if rec.start_time and rec.end_time and rec.end_time > rec.start_time:
                # convert float hours to total minutes
                start_minutes = int(rec.start_time * 60)
                end_minutes = int(rec.end_time * 60)
                duration = (end_minutes - start_minutes) / 60.0
            rec.duration = duration




