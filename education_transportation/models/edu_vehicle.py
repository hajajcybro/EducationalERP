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


class EduVehicle(models.Model):
    """ Class for trip  details """
    _name = 'edu.vehicle'
    _description = 'Vehicle'

    trip_rel_id = fields.Many2one('education.trip', string="Route",
                                  help="The route associated with this vehicle.")
    vehicle_id = fields.Many2one('fleet.vehicle', string='Vehicle',
                                 help="The vehicle used for the trip.")
    morning_timing = fields.Float(string="Morning Start Timing",
                                  help="The start time for the vehicle")
    evening_timing = fields.Float(string="Evening Start Timing",
                                  help="Evening start time for the vehicle")
    vehicle_no = fields.Char(string="Vehicle Code",
                             related='vehicle_id.vehicle_number',
                             help="The unique code for the vehicle.")
    driver_id = fields.Many2one('res.partner',
                                string="Driver", related='vehicle_id.driver_id',
                                help="The driver assigned to the vehicle.")
