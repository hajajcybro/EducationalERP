# -*- coding: utf-8 -*-
from odoo import models, fields,api
from odoo.exceptions import ValidationError
from datetime import timedelta

class EducationTimetable(models.Model):
    _name = 'education.timetable'
    _description = 'Weekly Timetable'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(required=True,help='eg:BSc 1st Year Timetable')
    class_id = fields.Many2one('education.class', string='Class')
    program_id = fields.Many2one('education.program', string='Program')
    session_id = fields.Many2one('education.session', string='Session')
    active = fields.Boolean(default=True)
    note =fields.Text()

