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


class EducationHostelMember(models.Model):
    """Created model 'education.hostel.member'"""
    _name = 'education.hostel.member'
    _rec_name = 'hostel_admission_no'
    _description = "Hostel Member"
    name = fields.Char(string="Name")
    member_type = fields.Selection(string='Member Type',
                                   selection=[('is_faculty', 'Faculty'),
                                              ('is_student', 'Student')],
                                   default='is_student', help="Select faculty"
                                                              "or student.")
    member_std_name = fields.Many2one('education.student',
                                      string="Admission No",
                                      domain=[('need_hostel', '=', True),
                                              ('hostel', '=', False)],
                                      help="Student admission number.")
    member_fac_name = fields.Many2one('education.faculty',
                                      string="Name", help="Faculty name.")
    email = fields.Char(string="Email")
    hostel_admission_no = fields.Char(string="Hostel Admission No",
                                      required=True, copy=False, readonly=True,
                                      index=True, default=lambda self: _('New'),
                                      help='Sequence of admission number.')
    phone = fields.Char(string="Phone")
    mobile = fields.Char(string="Mobile")
    image = fields.Binary("Image", attachment=True,
                          help="This field holds the image used as avatar"
                               " for this contact, limited to 1024x1024px")
    date_of_birth = fields.Date(string="Date Of birth")
    guardian_name = fields.Char(string="Guardian")
    father_name = fields.Char(string="Father")
    mother_name = fields.Char(string="Mother")
    gender = fields.Selection(
        [('male', 'Male'), ('female', 'Female'), ('other', 'Other')],
        string='Gender', required=True, default='male')
    blood_group = fields.Selection(
        [('a+', 'A+'), ('a-', 'A-'), ('b+', 'B+'), ('o+', 'O+'), ('o-', 'O-'),
         ('ab-', 'AB-'), ('ab+', 'AB+')],
        string='Blood Group', required=True,
        default='a+')
    street = fields.Char(string='Street')
    street2 = fields.Char(string='Street2')
    zip = fields.Char(string='Zip', change_default=True)
    city = fields.Char(string='City')
    state_id = fields.Many2one("res.country.state",
                               string='State')
    country_id = fields.Many2one('res.country', string='Country',
                                 )
    allocation_detail = fields.One2many('education.room_member',
                                        'room_member',
                                        string="Allocation_details")
    hostel = fields.Many2one('education.hostel', string="Hostel")
    room = fields.Many2one('education.room', string="Room")
    company_id = fields.Many2one('res.company', string='Company',
                                 default=lambda self: self.env[
                                     'res.company']._company_default_get())
    state = fields.Selection([('draft', 'Draft'), ('allocated', 'Allocated'),
                              ('vacated', 'Vacated')],
                             string='Status', default='draft')
    vacated_date = fields.Date(string="Vacated Date")

    @api.onchange('member_std_name')
    def onchange_student(self):
        """Onchange student information"""
        for student in self.member_std_name:
            self.email = student.email
            self.phone = student.phone
            self.mobile = student.mobile
            self.date_of_birth = student.date_of_birth
            self.guardian_name = student.guardian_id.name
            self.father_name = student.father_name
            self.mother_name = student.mother_name
            self.street = student.per_street
            self.zip = student.per_zip
            self.street2 = student.per_street2
            self.city = student.per_city
            self.state_id = student.per_state_id
            self.country_id = student.per_country_id
            self.gender = student.gender

    @api.onchange('member_fac_name')
    def onchange_faculty(self):
        """Onchange faculty name that updated the faculty details"""
        for student in self.member_fac_name:
            self.email = student.email
            self.phone = student.phone
            self.mobile = student.mobile
            self.date_of_birth = student.date_of_birth
            self.guardian_name = student.guardian_name
            self.father_name = student.father_name
            self.mother_name = student.mother_name
            self.gender = student.gender

    @api.model
    def create(self, vals):
        """Computing the name of the member"""
        if vals.get('hostel_admission_no', _('New')) == _('New'):
            vals['hostel_admission_no'] = self.env['ir.sequence'].next_by_code(
                'education.hostel.member') or _('New')

        if vals.get('member_std_name'):
            obj = self.env['education.student'].search(
                [('id', '=', vals.get('member_std_name'))])
        elif vals.get('member_fac_name'):
            obj = self.env['education.faculty'].search(
                [('id', '=', vals.get('member_fac_name'))])
        else:
            obj = False

        if obj:
            if obj._name == 'education.student':
                if obj.middle_name:
                    vals[
                        'name'] = obj.name + '  ' + obj.middle_name + '  ' + obj.last_name
                else:
                    vals['name'] = obj.name + '  ' + obj.last_name
            elif obj._name == 'education.faculty':
                vals['name'] = obj.name + ' ' + obj.last_name

        res = super(EducationHostelMember, self).create(vals)
        return res

    @api.onchange('member_std_name', 'member_fac_name')
    def name_change(self):
        """Computing the name of the member"""
        for name in self:
            if name.member_std_name:
                name.image = name.member_std_name.image_1920
                name.name = str(str(name.member_std_name.name) + ' ' + str(
                    name.member_std_name.last_name))
            if name.member_fac_name:
                name.name = str(
                    name.member_fac_name.name + ' ' + name.member_fac_name.last_name)

    @api.constrains('allocation_detail')
    def _check_capacity(self):
        """Getting the current room and Hostel"""
        if len(self.allocation_detail) != 0:
            self.hostel = self.allocation_detail[
                len(self.allocation_detail) - 1].hostel_room_rel.id
            self.room = self.allocation_detail[
                len(self.allocation_detail) - 1].room_member_rel.id
            self.vacated_date = self.allocation_detail[
                len(self.allocation_detail) - 1].vacated_date
            self.member_std_name.hostel_member = self.id
            self.member_std_name.hostel = self.hostel.id
            self.member_std_name.room = self.room.id
            self.member_std_name.hostel_fee = self.hostel.total

    def allocate_member(self):
        """Function to allocate member"""
        self.ensure_one()
        if self.allocation_detail:
            length = len(self.allocation_detail)
            if not self.allocation_detail[length - 1].allocated_date:
                raise ValidationError(_('Enter the Allocated Date'))
        return self.write({'state': 'allocated'})

    def vacate_member(self):
        """Function to vacate from hostel"""
        self.ensure_one()
        if self.allocation_detail:
            length = len(self.allocation_detail)
            if not self.allocation_detail[length - 1].vacated_date:
                raise ValidationError(_('Enter the Vacated Date'))
        return self.write({'state': 'vacated'})

    def reallocate(self):
        """Function to reallocate the hostel room"""
        return self.write({'state': 'draft'})
