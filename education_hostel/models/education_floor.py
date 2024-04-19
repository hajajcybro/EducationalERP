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


class EducationFloor(models.Model):
    """Created model 'education.floor' """
    _name = 'education.floor'
    _rec_name = "floor_no"
    _description = "Floor"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    floor_no = fields.Char(string="Floor", required=True,
                           help="Name of the floor.")
    hostel = fields.Many2one('education.hostel', required=True,
                             string="Hostel", help="Specify the hostel.")
    responsible = fields.Many2one('education.faculty',
                                  string="Responsible Staff",
                                  help="Responsible faculty of the floor.")

    company_id = fields.Many2one('res.company', string='Company',
                                 default=lambda s: s.env['res.company']._company_default_get('ir.sequence'),
                                 help="Default company.")

    @api.model
    def create(self, vals):
        """Check the floor count of hostel"""
        res = super(EducationFloor, self).create(vals)
        if vals['hostel']:
            floor = 0.0
            obj = self.env['education.hostel'].browse(vals['hostel'])
            floor_count = self.search_count([('hostel', '=', vals['hostel']),
                                             ('id', '!=', self.id)])
            if obj:
                floor += float(obj.hostel_floors)
                if floor < floor_count:
                    raise ValidationError(_('Floor Count is High'))
        return res
