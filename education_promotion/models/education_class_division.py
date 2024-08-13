# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
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
#############################################################################
from odoo import fields, models


class EducationClassDivision(models.Model):
    """ Inherits the model 'education.class.division' to add the fields. """
    _inherit = 'education.class.division'

    is_last_class = fields.Boolean(
        string="Is Last Class",
        help="Enable this option to set this class as last class")
    promote_class_id = fields.Many2one('education.class',
                                       string='Promotion Class',
                                       help='The promoted class for the student')
    promote_division_id = fields.Many2one('education.division',
                                          string='Promotion Division',
                                          help='The promoted division for '
                                               'the student')
    final_student_ids = fields.One2many('education.student.final.result',
                                        'division_id',
                                        string='Student Final Result',
                                        help='The student details for the '
                                             'final result.')
    active = fields.Boolean(
        'Active', default=True,
        help="If unchecked, it will allow you to hide the Academic "
             "Year without removing it.")
