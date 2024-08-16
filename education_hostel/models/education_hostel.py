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


class EducationHostel(models.Model):
    """Creates the model education.hostel"""
    _name = 'education.hostel'
    _rec_name = 'hostel_code'
    _description = "Hostel"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    hostel_name = fields.Char(string="Name", required=True, tracking=1,
                              help="Name of the hostel")
    hostel_code = fields.Char(string="Code", required=True, tracking=1,
                              help="Code of the hostel")
    hostel_capacity = fields.Char(string="Capacity",
                                  track_visibility='onchange',
                                  compute="_compute_student_total",
                                  help="Capacity of the hostel")
    hostel_floors = fields.Char(string="Total Floors",
                                help="Number of floors in the hostel",
                                required="1")
    hostel_rooms = fields.One2many('education.room_list', 'hostel_room_rel2',
                                   string="Rooms",
                                   help="List of rooms in the hostel")
    hostel_warden = fields.Many2one('education.faculty', required=True,
                                    string="Warden",
                                    track_visibility='onchange',
                                    help="Warden of the hostel")
    room_rent = fields.Char(string="Room Rent", required=True, tracking=1,
                            help="Rent of the hostel room")
    mess_fee = fields.Char(string="Mess Fee", required=True, tracking=1,
                           help="Mess fee of the hostel")
    total_students = fields.Char(string="Students",
                                 compute="_compute_student_total",
                                 help="Total students in the hostel")
    vacancy = fields.Char(string="Vacancy", compute="_compute_student_total",
                          help="Vacancy of students in the hostel")
    color = fields.Integer(string='Color Index',
                           help="Color index for students in the hostel")
    total = fields.Char(string="Total Fee", compute="_compute_fee_amount",
                        help="Total Fee of students in the hostel")
    total_rooms = fields.Char(string="Total Rooms",
                              compute="_compute_student_total",
                              help="Total Rooms in the hostel")
    street = fields.Char(string='Street', help="Street address of hostel")
    street2 = fields.Char(string='Street2', help="Street2 address of hostel")
    zip = fields.Char(string='Zip', change_default=True,
                      help="Zip code of the hostel")
    city = fields.Char(stirng='City', help="City of the hostel")
    state_id = fields.Many2one("res.country.state", string='State',
                               help="State of the hostel")
    country_id = fields.Many2one('res.country', string='Country',
                                 help="Country of the hostel")
    phone = fields.Char(string='Phone', required=1,
                        help="Phone number of the hostel")
    mobile = fields.Char(string='Mobile', required=1,
                         help="Mobile number of the hostel")
    email = fields.Char(string='Email', help="Email address of the hostel")
    company_id = fields.Many2one('res.company', string='Company',
                                 default=lambda self: self.env.company.id,
                                 help="Company of the hostel")

    @api.onchange('state_id')
    def _onchange_state_id(self):
        """Onchange method to work the state has been changed"""
        self.country_id = self.state_id.country_id.id

    def _compute_student_total(self):
        """compute the vacancy,total students and hostel capacity"""
        for rec in self:
            rec.total_rooms = len(rec.hostel_rooms)
            total_vacancy = 0
            allocated = 0
            capacity = 0
            for data in rec.hostel_rooms:
                allocated += int(data.room_mem_rel.allocated_number)
                capacity += int(data.room_mem_rel.room_capacity)
                total_vacancy += int(data.room_mem_rel.vacancy)
            rec.hostel_capacity = capacity
            rec.total_students = allocated
            rec.vacancy = total_vacancy
            if rec.hostel_capacity:
                rec.vacancy = capacity - allocated

    def _compute_fee_amount(self):
        """compute the fee amount"""
        for hst in self:
            if hst.room_rent and hst.mess_fee:
                hst.total = str(float(hst.room_rent) + float(hst.mess_fee))
            else:
                hst.total = 0

    def action_hostel_student_view(self):
        """shows the students in the hostel"""
        self.ensure_one()
        domain = [
            ('hostel', '=', self.id),
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
        }
