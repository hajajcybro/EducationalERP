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


class EducationHostStd(models.Model):
    """Creates the model education.host_std"""
    _name = 'education.host_std'
    _description = "Hostel Member"

    member_std_name = fields.Many2one('education.student',
                                      string="Admission No",
                                      domain="[('is_hostel_member', '=', False)]",
                                      help="Name of student")
    member_fac_name = fields.Many2one('education.faculty', string="Name",
                                      help="Name of faculty")
    name = fields.Char(string="Name", help="Name of hostel member")
    member_type = fields.Selection(string='Member Type',
                                   selection=[('is_faculty', 'Faculty'),
                                              ('is_student', 'Student')],
                                   default='is_student',
                                   help="Type of hostel member")
    email = fields.Char(string="Email", compute='_compute_member_details',
                        help="Email address of hostel member")
    hostel_admission_no = fields.Char(string="Hostel Admission No",
                                      required=True, copy=False, readonly=True,
                                      index=True, default=lambda self: _('New'),
                                      help="Admission number of hostel")
    phone = fields.Char(string="Phone", compute='_compute_member_details',
                        help="Phone number of hostel member")
    mobile = fields.Char(string="Mobile", compute='_compute_member_details',
                         help="Mobile number of hostel member")
    image = fields.Binary("Image", attachment=True,
                          help="This field holds the image used as avatar for "
                               "this contact, limited to 1024x1024px")
    date_of_birth = fields.Date(string="Date of Birth",
                                compute='_compute_member_details',
                                help="Date of Birth of hostel member")
    guardian_name = fields.Char(string="Guardian",
                                compute='_compute_member_details',
                                help="Guardian of hostel member")
    father_name = fields.Char(string="Father",
                              compute='_compute_member_details',
                              help="Fathers name of hostel member")
    mother_name = fields.Char(string="Mother",
                              related='member_std_name.mother_name',
                              help="Mothers name of hostel member")
    gender = fields.Selection(
        [('male', 'Male'), ('female', 'Female'), ('other', 'Other')],
        string='Gender', required=True, default='male',
        track_visibility='onchange',
        compute='_compute_member_details', help="Gender of the hostel member")
    blood_group = fields.Selection(
        [('a+', 'A+'), ('a-', 'A-'), ('b+', 'B+'), ('o+', 'O+'), ('o-', 'O-'),
         ('ab-', 'AB-'), ('ab+', 'AB+')],
        string='Blood Group', required=True, default='a+',
        track_visibility='onchange', help="Blood group of the hostel member")
    street = fields.Char(string='Street', compute='_compute_member_details',
                         help="Street of the hostel member")
    street2 = fields.Char(string='Street2',
                          related='member_std_name.per_street2',
                          help="Street2 of the hostel member")
    zip = fields.Char(string='Zip', change_default=True,
                      related='member_std_name.per_zip',
                      help="Zip of the hostel member")
    city = fields.Char(string='City', related='member_std_name.per_city',
                       help="City of the hostel member")
    state_id = fields.Many2one("res.country.state", string='State',
                               related='member_std_name.per_state_id',
                               help="State of the hostel member")
    country_id = fields.Many2one('res.country', string='Country',
                                 related='member_std_name.per_country_id',
                                 help="Country of the hostel member")
    allocation_detail = fields.One2many('education.room_member', 'room_member',
                                        string="Allocation details",
                                        readonly=True,
                                        help="Allocation details of the "
                                             "hostel member")
    hostel = fields.Many2one('education.hostel', string="Hostel",
                             related='room.hostel', help="Hostel of the member")
    room = fields.Many2one('education.room', string="Room",
                           help="Room of the member")
    company_id = fields.Many2one('res.company', string='Company',
                                 default=lambda self: self.env.company.id,
                                 help="Company of the hostel")
    state = fields.Selection([('draft', 'Draft'), ('allocated', 'Allocated'),
                              ('vacated', 'Vacated')],
                             string='Status', default='draft',
                             help="State of the hostel member")
    vacated_date = fields.Date(string="Vacated Date",
                               related='current_allocation_id.vacated_date',
                               help="Vacated date of the hostel member")
    allocated_date = fields.Date(string="Allocated Date",
                                 related='current_allocation_id.allocated_date',
                                 help="Allocated date of the hostel member")
    current_allocation_id = fields.Many2one('education.room_member',
                                            string="Current Allocation",
                                            help="Current allocation of the "
                                                 "student", readonly=True)

    @api.depends('member_std_name', 'member_fac_name')
    def _compute_member_details(self):
        """Method _compute_member_details to compute the values of the member
        details"""
        for rec in self:
            if rec.member_type == 'is_faculty':
                rec.mobile = rec.member_fac_name.mobile
                rec.street = False
                rec.gender = rec.member_fac_name.gender
                rec.date_of_birth = rec.member_fac_name.date_of_birth
                rec.father_name = rec.member_fac_name.father_name
                rec.guardian_name = rec.member_fac_name.guardian_name
                rec.phone = rec.member_fac_name.phone
                rec.email = rec.member_fac_name.email
            elif rec.member_type == 'is_student':
                rec.mobile = rec.member_std_name.mobile
                rec.street = rec.member_std_name.street
                rec.gender = rec.member_std_name.gender
                rec.date_of_birth = rec.member_std_name.date_of_birth
                rec.father_name = rec.member_std_name.father_name
                rec.guardian_name = rec.member_std_name.guardian_name.name
                rec.email = rec.member_std_name.email
                rec.phone = rec.member_std_name.phone

    @api.model
    def create(self, vals):
        """computing the name of the member"""
        if vals.get('hostel_admission_no', _('New')) == _('New'):
            vals['hostel_admission_no'] = self.env['ir.sequence'].next_by_code(
                'education.host_std') or _('New')
        if vals.get('member_std_name'):
            obj = self.env['education.student'].browse(
                vals.get('member_std_name'))
            if obj.middle_name:
                vals[
                    'name'] = obj.name + '  ' + obj.middle_name + '  ' + obj.last_name
            else:
                vals['name'] = obj.name + '  ' + obj.last_name
        elif vals.get('member_fac_name'):
            obj = self.env['education.faculty'].browse(
                vals.get('member_fac_name'))
            vals['name'] = obj.name + ' ' + obj.last_name
        res = super(EducationHostStd, self).create(vals)
        res.member_std_name.is_hostel_member = True
        return res

    def unlink(self):
        """Supering the unlink method to remove the is hostel member boolean
        from the model student that the user is a hostel member"""
        for rec in self:
            if rec.member_std_name.is_hostel_member:
                rec.member_std_name.is_hostel_member = False
        return super().unlink()

    @api.onchange('member_std_name', 'member_fac_name')
    def _onchange_member_std_name(self):
        """computing the name of the member"""
        for rec in self:
            if rec.member_std_name:
                rec.image = rec.member_std_name.image_1920
                rec.name = str(str(rec.member_std_name.name) + ' ' + str(
                    rec.member_std_name.last_name))
            elif rec.member_fac_name:
                rec.name = str(
                    rec.member_fac_name.name + ' ' + rec.member_fac_name.last_name)

    def action_allocate_member(self):
        """Method allocate_member to allocate the member to a room"""
        self.ensure_one()
        if self.room:
            allocation = self.env['education.room_member'].create({
                'room_member_rel': self.room.id,
                'allocated_date': fields.Date.today(),
                'room_member': self.id,
            })
            self.current_allocation_id = allocation.id
            self.state = 'allocated'
        else:
            raise ValidationError(
                _("There is no room selected, please select a room"))

    def action_vacate_member(self):
        """Method vacate_member to vacate the member from the room"""
        self.ensure_one()
        if self.current_allocation_id:
            self.current_allocation_id.vacated_date = fields.Date.today()
            self.state = 'vacated'
        else:
            raise ValidationError(
                _("There are not current allocation for this student"))

    def action_reallocate(self):
        """Method action_reallocate to relocate the member to a room"""
        self.current_allocation_id = False
        self.room = False
        return self.write({'state': 'draft'})
