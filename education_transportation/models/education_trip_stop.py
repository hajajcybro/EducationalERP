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


class EducationTripStop(models.Model):
    """Represents a stop within a specific trip in the educational
    transportation system."""
    _name = 'education.trip_stop'
    _rec_name = "stop_id"
    _order = 'stop_sequence'

    stop_id = fields.Many2one('education.stop', string="Name",
                              required=True, help="Select the name of "
                                                  "the stop")
    stop_sequence = fields.Integer(string='Sequence',
                                   related='stop_id.stop_sequence',
                                   help="Sequence of the stop within the trip.")
    cost = fields.Float(string="Cost",
                        related='stop_id.cost',
                        help="Cost for the trip")
    stop_trip_rel_id = fields.Many2one('education.trip', string="Trip",
                                       help="The trip to which this stop "
                                            "belongs.")
    morning_timing = fields.Float(string="Duration from Source",
                                  help="Duration in the morning")
    evening_timing = fields.Float(string="Duration from Destination",
                                  help="Duration in the evening.")
