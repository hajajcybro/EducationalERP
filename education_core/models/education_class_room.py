# -*- coding: utf-8 -*-
from odoo import api, fields, models,_
from odoo.exceptions import ValidationError

class EducationClassRoom(models.Model):
    _name = 'education.class.room'
    _description = 'Education Class Room'

    name = fields.Integer(string='Room Name', required=True)
    building = fields.Char(string='Building', help='Building or block name')
    floor = fields.Char(string='Floor', help='Floor number', required=True)
    capacity = fields.Integer(string='Room Capacity', required=True)
    notes = fields.Text(string='Notes')
    active = fields.Boolean(string='Active', default=True)


    @api.constrains('capacity')
    def _check_capacity(self):
        for record in self:
            if record.capacity <= 0:
                raise ValidationError('Capacity must be greater than zero.')

