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


class EducationHostel(models.Model):
    """Created model 'education.hostel'"""
    _name = 'education.hostel'
    _rec_name = 'hostel_name'
    _description = "Hostel"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    hostel_name = fields.Char(string="Name", required=True, tracking=True,
                              help="Name of the hostel.")
    hostel_code = fields.Char(string="Code", required=True, tracking=True,
                              help="Code of the hostel.")
    hostel_capacity = fields.Char(string="Capacity"
                                  , compute="_compute_student_total",
                                  help="Capacity of the hostel.")
    hostel_floors = fields.Char(string="Total Floors", required=True,
                                help="Total floors inside hostel.")
    hostel_room_ids = fields.One2many('education.room_list',
                                      'hostel_room_rel2',
                                      string="Rooms",
                                      help="Hostel rooms.")
    hostel_warden_id = fields.Many2one('education.faculty',
                                       required=True, string="Warden",
                                       help="Warden of the hostel.")
    room_rent = fields.Char(string="Room Rent", required=True, tracking=True,
                            help="Room rent of the hostel.")
    mess_fee = fields.Char(string="Mess Fee", required=True, tracking=True,
                           help="Mess fee of the mess.")
    total_students = fields.Char(string="Students",
                                 compute="_compute_student_total",
                                 help="Total students of the hostel.")
    vacancy = fields.Char(string="Vacancy", compute="_compute_student_total",
                          help="Vacancy of the hostel.")
    color = fields.Integer(string='Color Index', help='Color index of hostel')
    total = fields.Char(string="Total Fee", compute="_compute_fee_amount",
                        help="Total fee.")
    total_rooms = fields.Char(string="Total Rooms",
                              compute="_compute_student_total",
                              help="Total Rooms inside hostel.")
    street = fields.Char(string='Street', help='Street of hostel')
    street2 = fields.Char(string='Street2', help='Street2 of hostel')
    zip = fields.Char(string='Zip', change_default=True, help='Zip of hostel')
    city = fields.Char(string='City', help='City of hostel')
    state_id = fields.Many2one("res.country.state", string='State',
                               help='State of hostel')
    country_id = fields.Many2one('res.country', string='Country',
                                 help='Country of hostel')
    phone = fields.Char(string='Phone', required=True, help='Phone of hostel')
    mobile = fields.Char(string='Mobile', required=True,
                         help='Mobile of hostel')
    email = fields.Char(string='Email', help='Email of hostel')
    company_id = fields.Many2one('res.company', string='Company',
                                 default=lambda s: s.env[
                                     'res.company']._company_default_get(
                                     'ir.sequence'),
                                 help='Company corresponding to the hostel')

    def _compute_student_total(self):
        """Compute the vacancy,total students and hostel capacity"""
        for dt in self:
            dt.total_rooms = len(dt.hostel_room_ids)
            total_vacancy = 0
            allocated = 0
            capacity = 0
            for data in dt.hostel_room_ids:
                allocated += int(data.room_mem_rel.allocated_number)
                capacity += int(data.room_mem_rel.room_capacity)
                total_vacancy += int(data.room_mem_rel.vacancy)
            dt.hostel_capacity = capacity
            dt.total_students = allocated
            dt.vacancy = total_vacancy
            if dt.hostel_capacity:
                dt.vacancy = capacity - allocated

    def _compute_fee_amount(self):
        """Compute the fee amount"""
        for hst in self:
            if hst.room_rent and hst.mess_fee:
                hst.total = str(float(hst.room_rent) + float(hst.mess_fee))

    @api.model
    def create(self, vals):
        """Overriding  the create method to show the validation error """
        res = super(EducationHostel, self).create(vals)
        if not vals['hostel_floors']:
            raise ValidationError(_('Enter the Total Floors'))
        if not vals['phone']:
            raise ValidationError(_('Enter the Phone Number'))
        if not vals['mobile']:
            raise ValidationError(_('Enter the Mobile Number'))
        return res

    def action_view_hostel_student(self):
        """Shows the students in the hostel"""
        self.ensure_one()
        domain = [
            ('hostel_id', '=', self.id),
            ('state', '=', 'allocated'),
            ('vacated_date', '=', False)]
        return {
            'name': _('Students'),
            'domain': domain,
            'res_model': 'education.hostel.member',
            'type': 'ir.actions.act_window',
            'view_id': False,
            'view_mode': 'tree,form',
            'view_type': 'tree',
            'context': "{'default_room': '%s'}" % self.id
        }
