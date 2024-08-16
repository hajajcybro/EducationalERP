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


class EducationRoom(models.Model):
    """Creates the model education.room"""
    _name = 'education.room'
    _rec_name = 'room_name'
    _description = "Room"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    hostel = fields.Many2one('education.hostel', required=True, string="Hostel",
                             help="Hostel Name")
    room_name = fields.Char(string="Room Name", required=True,
                            track_visibility='onchange',
                            help="Name of the room")
    room_code = fields.Char(string="Room Code", required=True,
                            track_visibility='onchange',
                            help="Code of the room")
    floor = fields.Many2one('education.floor', required=True, string="Floor",
                            domain="[('hostel', '=', hostel)]",
                            help="Floor of the room")
    responsible = fields.Many2one('education.faculty',
                                  string="Responsible Staff",
                                  related='floor.responsible',
                                  help="Responsible person of the room.")
    room_capacity = fields.Char(string="Capacity", required=True,
                                track_visibility='onchange',
                                help="Room capacity")
    room_members = fields.One2many('education.room_member', "room_member_rel",
                                   string="Room members",
                                   track_visibility='onchange',
                                   help="Members of the room")
    room_amenity = fields.One2many('room.amenity', 'amenity_rel',
                                   track_visibility='onchange',
                                   string="Amenities",
                                   help="Amenities of the room")
    allocated_number = fields.Integer(string="Allocated Students",
                                      compute='_compute_allocated_number',
                                      help="Number of Allocated Students to "
                                           "the room")
    vacancy = fields.Char(string="Vacancy", compute='_compute_vacancy',
                          help="Number of Vacancies in the room")
    company_id = fields.Many2one('res.company', string='Company',
                                 default=lambda self: self.env.company.id,
                                 help="Company of the room")

    def _compute_allocated_number(self):
        """method _compute_allocated_number to compute the value to the field
        allocated number"""
        for rec in self:
            rec.allocated_number = self.env['education.host_std'].search_count(
                [('room', '=', rec.id),
                 ('state', 'not in', ['vacated'])])

    @api.constrains('room_members')
    def _compute_vacancy(self):
        """counting the allocated and vacancy for room"""
        for std in self:
            std_count = self.env['education.host_std'].search_count(
                [('room', '=', std.id),
                 ('state', '!=', 'vacated'),
                 ('vacated_date', '=', False)])
            if std_count > int(std.room_capacity):
                raise ValidationError(_('Room Capacity is Over'))
            std.allocated_number = std_count
            std.vacancy = int(std.room_capacity) - std_count

    @api.model
    def create(self, vals):
        """Supering the create method to create record in the model education
        room list"""
        res = super(EducationRoom, self).create(vals)
        if 'hostel' in vals and vals['hostel']:
            self.env['education.room_list'].create({
                'room_mem_rel': res.id,
                'floor': res.floor.id,
                'hostel_room_rel2': vals['hostel']
            })
        return res

    def action_student_view(self):
        """get the students allocated in the room"""
        self.ensure_one()
        domain = [
            ('room', '=', self.id),
            ('state', '=', 'allocated'),
            ('vacated_date', '=', False)]
        return {
            'name': _('Students'),
            'domain': domain,
            'res_model': 'education.host_std',
            'type': 'ir.actions.act_window',
            'view_id': False,
            'view_mode': 'tree,form',
            'view_type': 'form',
            'context': {'default_room': self.id}
        }


class EducationRoomList(models.Model):
    """Creates the model education.room_list which shows the rooms of a
    hostel in the hostel form view"""
    _name = 'education.room_list'
    _description = 'Education Room List'
    _rec_name = 'room_mem_rel'

    room_mem_rel = fields.Many2one('education.room', string="Room",
                                   help="Room for the education")
    floor = fields.Many2one('education.floor', string="Floor",
                            related='room_mem_rel.floor',
                            help="Floor of the room")
    hostel_room_rel2 = fields.Many2one('education.hostel', string="Room",
                                       related='room_mem_rel.hostel',
                                       help="Hostel of the room")


class EducationRoomMember(models.Model):
    """Creates the model education.room_member"""
    _name = 'education.room_member'
    _rec_name = 'room_member'
    _description = "Room Member"

    room_member_rel = fields.Many2one('education.room', string="Room",
                                      help="Room for the member")
    allocated_date = fields.Date(string="Allocated Date",
                                 help="Allocated date of the room member")
    vacated_date = fields.Date(string="Vacated Date",
                               help="Vacated date of the room member")
    room_member = fields.Many2one('education.host_std', string="Member",
                                  help="Member of the room")
    floor = fields.Many2one('education.floor', string="Floor",
                            related='room_member_rel.floor',
                            help="Floor of the room")
    hostel_room_rel = fields.Many2one('education.hostel', string="Hostel",
                                      related='room_member_rel.hostel',
                                      help="Hostel of the room")
    student_id = fields.Many2one('education.student', string="Student",
                                 help="Student in the room")

    @api.onchange('hostel_room_rel')
    def onchange_hostel_room_rel(self):
        """adding domain for room"""
        hostel = None
        if self.hostel_room_rel:
            hostel = self.hostel_room_rel.id
        return {
            'domain': {
                'room_member_rel': [('hostel', '=', hostel)]
            }
        }


class EducationRoomAmenity(models.Model):
    """Creates the model room.amenity"""
    _name = 'room.amenity'
    _description = "Amenity"

    amenity = fields.Many2one('education.amenities', string="Amenity",
                              required=True, help="Amenities in the room")
    qty = fields.Integer(string="Quantity", default=1,
                         help="Quantity of amenities")
    amenity_rel = fields.Many2one('education.room', string="Room",
                                  help="Room of amenities")

    @api.constrains('qty')
    def check_qty(self):
        """Method check_qty to check the quantity"""
        for rec in self:
            if rec.qty <= 0:
                raise ValidationError(_('Quantity must be positive'))
