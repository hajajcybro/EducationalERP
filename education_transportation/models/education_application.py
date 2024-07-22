# -*- coding: utf-8 -*-
##############################################################################
#    A part of Educational ERP Project <https://www.educationalerp.com>

#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Subina P (odoo@cybrosys.com)
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
##############################################################################
from odoo import fields, models


class EducationApplication(models.Model):
    """Inherited class of education application to add transportation """
    _inherit = 'education.application'

    need_transportation_facility = fields.Boolean(
        string='Need Transportation Facility',
        help="Enable true if "
             "the transportation "
             "facility requires")

    def create_student(self):
        """extends the create_student method from the EducationApplication.
    It checks if the applicant requires a transportation facility and updates
    corresponding student's record to reflect this requirement"""
        for rec in self:
            res = super(EducationApplication, rec).create_student()
            if rec.need_transportation_facility:
                std = self.env['education.student'].search(
                    [('application_id', '=', rec.id)])
                if std:
                    std.need_transportation_facility = True
            return res
