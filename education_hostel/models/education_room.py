# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Jumana Haseen (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
################################################################################
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class EducationRoom(models.Model):
    """Creating a model 'education.room' with fields"""
    _name = 'education.room'
    _rec_name = 'room_name'
    _description = "Room"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    hostel = fields.Many2one('education.hostel', required=True,
                             string="Hostel")
    room_name = fields.Char(string="Room Name", required=True, )
    room_code = fields.Char(string="Room Code", required=True)
    floor = fields.Many2one('education.floor', required=True, string="Floor")
    responsible = fields.Many2one('education.faculty',
                                  string="Responsible Staff",
                                  related='floor.responsible')
    room_capacity = fields.Char(string="Capacity", required=True)
    room_members = fields.One2many('education.room_member', "room_member_rel")
    room_amenity = fields.One2many('room.amenity', 'amenity_rel')
    allocated_number = fields.Char(string="Allocated Students",
                                   compute='get_total_allocated')
    vacancy = fields.Char(string="Vacancy", compute='get_total_allocated')
    company_id = fields.Many2one('res.company', string='Company',
                                 default=lambda self: self.env[
                                     'res.company']._company_default_get())

    @api.onchange('hostel', 'floor')
    def get_rooms(self):
        """Adding domain for floors"""
        hostel = None
        if self.hostel:
            hostel = self.hostel.id
        return {
            'domain': {
                'floor': [('hostel', '=', hostel)]
            }
        }

    @api.constrains('room_members')
    def get_total_allocated(self):
        """Counting the allocated and vacancy for room"""
        for std in self:
            std_count = self.env['education.hostel.member'].search_count(
                [('room', '=', std.id),
                 ('state', '!=', 'vacated'),
                 ('vacated_date', '=', False)])
            if std_count > int(std.room_capacity):
                raise ValidationError(_('Room Capacity is Over'))
            std.allocated_number = std_count
            std.vacancy = int(std.room_capacity) - std_count

    @api.model
    def create(self, vals):
        """Function to create education room list"""
        res = super(EducationRoom, self).create(vals)
        if 'hostel' in vals and vals['hostel']:
            self.env['education.room_list'].create({
                'room_mem_rel': res.id,
                'floor': res.floor.id,
                'hostel_room_rel2': vals['hostel']
            })
        return res

    # @api.multi
    def student_view(self):
        """Get the students allocated in the room"""
        self.ensure_one()
        domain = [
            ('room', '=', self.id),
            ('state', '=', 'allocated'),
            ('vacated_date', '=', False)]
        return {
            'name': _('Students'),
            'domain': domain,
            'res_model': 'education.hostel.member',
            'type': 'ir.actions.act_window',
            'view_id': False,
            'view_mode': 'tree,form',
            'view_type': 'form',
            'context': "{'default_room': '%s'}" % self.id
        }


class EduAmen(models.Model):
    """Model created  'edu.amenity'"""
    _name = 'edu.amenity'
    _description = "Amenity"

    name = fields.Char(string="Amenity")
