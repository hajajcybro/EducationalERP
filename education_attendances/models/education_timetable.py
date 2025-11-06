# -*- coding: utf-8 -*-
from odoo import models, fields,api
from odoo.exceptions import ValidationError
from datetime import timedelta

class EducationTimetable(models.Model):
    _name = 'education.timetable'
    _description = 'Weekly Timetable'

    name = fields.Char(required=True,help='eg:BSc 1st Year Timetable')
    class_id = fields.Many2one('education.class', string='Class')
    program_id = fields.Many2one('education.program')
    start_date = fields.Date(required=True)
    end_date = fields.Date(required=True)
    line_ids = fields.One2many('education.timetable.line', 'template_id', string='Time Slots')
    slot_ids = fields.One2many("education.timetable.slot", "template_id", string="Generated Slots")
    active = fields.Boolean(default=True)


    @api.constrains('start_time', 'end_time')
    def _check_time_order(self):
        """Validate that start time is earlier than end time."""
        for rec in self:
            if rec.start_time >= rec.end_time:
                raise ValidationError("Start time must be earlier than end time.")


    @api.model
    def _cron_generate_weekly_slots(self):
        print('hello')
    #     print('cron activate')
    #     """Automatically generate next week's timetable slots."""
    #     today = fields.Date.today()
    #     templates = self.search([
    #         ('start_date', '<=', today),
    #         ('end_date', '>=', today),
    #         ('active', '=', True)
    #     ])
    #     weekday_map = {
    #         'monday': 0, 'tuesday': 1, 'wednesday': 2,
    #         'thursday': 3, 'friday': 4
    #     }
    #     for template in templates:
    #         start = fields.Date.from_string(today)
    #         end = start + timedelta(days=7)
    #
    #         for line in template.line_ids:
    #             day_num = weekday_map.get(line.day)
    #             current = start
    #             while current <= end:
    #                 if current.weekday() == day_num:
    #                         slot=self.env['education.timetable.slot'].create({
    #                             'template_id': template.id,
    #                             'date': current,
    #                             'faculty_id': line.faculty_id.id,
    #                             'start_time': line.start_time,
    #                             'end_time': line.end_time,
    #                             'class_id': template.class_id.id,
    #                         })
    #
    #
    #                 current += timedelta(days=1)
    #
    #
    #     print('Timetable slot generation completed')
    #     return True

