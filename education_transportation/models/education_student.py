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


class EducationStudent(models.Model):
    """Extends the education.student model to include transportation details."""
    _inherit = 'education.student'

    trip_id = fields.Many2one('education.trip', string="Route",
                              track_visibility='onchange',
                              help="Select the route assigned to the student")
    location_id = fields.Many2one('education.stop', string='Location',
                                  track_visibility='onchange',
                                  help="Select the stop location_id for"
                                       " the student.")
    trans_cost = fields.Float(string="Transportation Fee",
                              related='location_id.cost',
                              track_visibility='onchange',
                              help="The transportation fee based on the stop "
                                   "location.")
    need_transportation_facility = fields.Boolean(
        string='Need Transportation Facility',
        help="Indicate if the student"
             "needs transportation "
             "services.")
