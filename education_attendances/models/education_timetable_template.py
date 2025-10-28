# -*- coding: utf-8 -*-
from odoo import models, fields,api
from odoo.exceptions import ValidationError
from datetime import timedelta

class EducationTimetableTemplate(models.Model):
    _name = 'education.timetable.template'
    _description = 'Weekly Timetable Template'

    name = fields.Char(required=True,help='eg:BSc 1st Year Timetable')
    class_id = fields.Many2one('education.class', required=True)
    start_date = fields.Date(required=True)
    end_date = fields.Date(required=True)
    line_ids = fields.One2many('education.timetable.line', 'template_id', string='Time Slots')
    active = fields.Boolean(default=True)

    def action_generate_slots(self):
        """Generate timetable slots for all weeks between start_date and end_date."""
        slot = self.env['education.timetable.slot']
        for template in self:
            if not template.start_date or not template.end_date:
                raise ValueError("Please set both start and end dates for the template.")
            current_date = template.start_date
            while current_date <= template.end_date:
                weekday = current_date.strftime('%A').lower()
                # Loop through lines matching the weekday
                for line in template.line_ids.filtered(lambda l: l.day == weekday):
                    # Avoid duplicate slot creation
                    existing = slot.search([
                        ('date', '=', current_date),
                        ('class_id', '=', template.class_id.id),
                        ('subject_id', '=', line.subject_id.id),
                        ('faculty_id', '=', line.faculty_id.id),
                        ('start_time', '=', line.start_time),
                    ], limit=1)
                    if not existing:
                        slot.create({
                            'date': current_date,
                            'class_id': template.class_id.id,
                            'subject_id': line.subject_id.id,
                            'faculty_id': line.faculty_id.id,
                            'room_id': line.room_id.id,
                            'start_time': line.start_time,
                            'end_time': line.end_time,
                            'status': 'scheduled',
                        })
                current_date += timedelta(days=1)
        return True

    @api.constrains('start_time', 'end_time')
    def _check_time_order(self):
        """Validate that start time is earlier than end time."""
        for rec in self:
            if rec.start_time >= rec.end_time:
                raise ValidationError("Start time must be earlier than end time.")


