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
from odoo import fields, models


class EducationApplication(models.Model):
    """Inherits the model education.application"""
    _inherit = 'education.application'

    need_hostel = fields.Boolean(string='Need Hostel Facility',
                                 help='If the student need hostel facility')

    def create_student(self):
        """creating hostel admission from the student application form"""
        for rec in self:
            res = super(EducationApplication, rec).create_student()
            if rec.need_hostel:
                std = self.env['education.student'].search(
                    [('application_id', '=', rec.id)])
                if std:
                    std.need_hostel = True
                    values = {
                        'member_std_name': std.id,
                        'blood_group': std.blood_group,
                        'image': std.image_1920,
                    }
                    self.env['education.host_std'].create(values)
            return res


class EducationStudent(models.Model):
    """Inherits the model education.student"""
    _inherit = 'education.student'

    need_hostel = fields.Boolean(string='Need Hostel Facility',
                                 help="Whether need hostel facility for "
                                      "student")
    hostel = fields.Many2one('education.hostel', string="Hostel", tracking=1,
                             help="Hostel of the student")
    room = fields.Many2one('education.room', string="Room", tracking=1,
                           help="Room of the student")
    hostel_fee = fields.Char(string="Fee", tracking=1,
                             help="Fee of the student")
    hostel_member = fields.Many2one('education.host_std',
                                    string="Hostel Admission No",
                                    help="Hostel Member of the student")
    is_hostel_member = fields.Boolean(string='Is Hostel Member',
                                      help="Is already a hostel member")
