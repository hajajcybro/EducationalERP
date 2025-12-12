# -*- coding: utf-8 -*-
from odoo import models, fields

class EducationTransportAssignment(models.Model):
    _name = 'education.transport.assignment'
    _description = 'Student Transport Assignment'
    _rec_name = 'student_id'

    student_id = fields.Many2one(
        'res.partner',
        string="Student",
        required=True
    )
    route_id = fields.Many2one(
        'education.transport.route',
        string="Route",
        required=True
    )
    stop_id = fields.Many2one(
        'education.transport.stop',
        string="Stop",
        required=True
    )
    active = fields.Boolean(string="Active", default=True)
    notes = fields.Text(string="Notes")
