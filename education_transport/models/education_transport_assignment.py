# -*- coding: utf-8 -*-
from odoo import models, fields, api,_
from odoo.exceptions import ValidationError

class EducationTransportAssignment(models.Model):
    _name = 'education.transport.assignment'
    _description = 'Student Transport Assignment'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'student_id'

    student_id = fields.Many2one(
        'res.partner',
        string="Student",
        required=True,
        domain = [('is_student', '=', True)]
    )
    image = fields.Image()
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

    @api.onchange('student_id')
    def _onchange_student_id_set_image(self):
        """  Automatically update the record image when a student is selected."""
        for rec in self:
            if rec.student_id:
                rec.image = rec.student_id.image_1920
            else:
                rec.image = False

    @api.constrains('student_id', 'route_id', 'active')
    def _check_unique_student_route(self):
        """Prevent assigning the same student to multiple active routes."""
        for record in self:
            domain = [
                ('student_id', '=', record.student_id.id),
                ('active', '=', True),
                ('id', '!=', record.id),
            ]
            if self.search_count(domain):
                raise ValidationError(
                    _("This student is already assigned to another active transport route.")
                )

