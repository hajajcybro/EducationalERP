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


class EducationStop(models.Model):
    """Class for representing stop in the educational transportation system."""
    _name = 'education.stop'
    _rec_name = "stop_id"
    _order = 'stop_sequence'
    _description = "Stage"

    stop_id = fields.Many2one('edu.stop', string="Stage Name",
                              required=True,
                              help="Select the name of the stop.")
    stop_sequence = fields.Integer(string='Sequence',
                                   help="Define the sequence of the stop in "
                                        "the route.")
    cost = fields.Float(string="Cost", help="Enter the cost associated with "
                                            "the stop.")
    company_id = fields.Many2one('res.company', string='Company',
                                 help="Select the company associated with "
                                      "this stop.",
                                 default=lambda s: s.env[
                                     'res.company']._company_default_get(
                                     'ir.sequence'))
