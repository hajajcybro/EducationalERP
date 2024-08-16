# -*- coding: utf-8 -*-
################################################################################
#    A part of Educational ERP Project <https://www.educationalerp.com>
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Arjun S(<https://www.cybrosys.com>)
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
################################################################################
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class EducationFloor(models.Model):
    """Creates the model education.floor"""
    _name = 'education.floor'
    _rec_name = "floor_no"
    _description = "Floor"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    floor_no = fields.Char(string="Floor", required=True,
                           help="Number of the floor")
    hostel = fields.Many2one('education.hostel', required=True, string="Hostel",
                             help="Hostel which the floor belongs")
    responsible = fields.Many2one('education.faculty',
                                  string="Responsible Staff",
                                  track_visibility='onchange',
                                  help="Responsible person of the hostel floor")
    company_id = fields.Many2one('res.company', string='Company',
                                 default=lambda self: self.env.company.id,
                                 help="Company which the record belongs to")

    @api.model
    def create(self, vals):
        """check the floor count of hostel"""
        res = super(EducationFloor, self).create(vals)
        if vals['hostel']:
            floor = 0.0
            obj = self.env['education.hostel'].browse(vals['hostel'])
            floor_count = self.search_count(
                [('hostel', '=', vals['hostel']), ('id', '!=', self.id)])
            if obj:
                floor += float(obj.hostel_floors)
                if floor < floor_count:
                    raise ValidationError(_('Floor Count is High'))
        return res
