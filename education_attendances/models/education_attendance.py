# -*- coding: utf-8 -*-
from odoo import models, fields, api

class EducationAttendance(models.Model):
    _name = 'education.attendance'
    _description = 'Education Attendance'

    student_id = fields.Many2one('res.partner', required=True, domain=[('position_role', '=', 'student')])
    roll_no = fields.Char()
    present = fields.Boolean(string='Present/Absence', default=True)

