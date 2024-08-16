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


class EducationMess(models.Model):
    """Creates the model education.mess"""
    _name = 'education.mess'
    _rec_name = "mess_code"
    _description = "Mess"

    mess_name = fields.Char(string="Name", required="True",
                            help="Name of the Mess")
    mess_code = fields.Char(string="Code", required="True",
                            help="Code of the Mess")
    food_menu = fields.One2many('mess.food', 'mess_rel', string="Food Menu",
                                help="Food Menu in the Mess")
    hostel = fields.Many2one('education.hostel', string="Hostel",
                             required="True", help="Hostel of the Mess")
    company_id = fields.Many2one('res.company', string='Company',
                                 default=lambda self: self.env.company.id,
                                 help="Company of the Education Mess")


class FoodItem(models.Model):
    """Creates the model food.item"""
    _name = 'food.item'
    _description = 'Food'

    name = fields.Char(String="Food", required=True,
                       help="Name of the Food Item")


class MessFood(models.Model):
    """Creates the model mess.food"""
    _name = 'mess.food'
    _description = 'Food Order'

    mess_rel = fields.Many2one('education.mess', string="MESS",
                               help="Name of the Mess")
    break_fast = fields.Many2one('food.item', string="Break Fast",
                                 help="Break Fast food")
    lunch = fields.Many2one('food.item', string="Lunch", help="Food for lunch")
    snack = fields.Many2one('food.item', string="Snack", help="Food for snack")
    supper = fields.Many2one('food.item', string="Supper",
                             help="Food for supper")
    week_list = fields.Selection([
        ('MO', 'Monday'),
        ('TU', 'Tuesday'),
        ('WE', 'Wednesday'),
        ('TH', 'Thursday'),
        ('FR', 'Friday'),
        ('SA', 'Saturday'),
        ('SU', 'Sunday')
    ], string='Weekday', help="Weekday of the week", required=True)
