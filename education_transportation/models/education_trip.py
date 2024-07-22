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
###############################################################################
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class EducationTrip(models.Model):
    _name = 'education.trip'
    _description = "Route"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Route', size=32, default='New',
                       help="Enter name of route")
    stop_ids = fields.One2many('education.trip_stop', 'stop_trip_rel_id',
                               string='Stops',
                               help="List of stops included in this"
                                    " route.")
    src_loc_id = fields.Many2one('education.stop', string='From',
                                 required=True, help="Starting location")
    dest_loc_id = fields.Many2one('education.stop', string='To',
                                  required=True, help="Destination")
    total_students = fields.Char(string="Total Students", readonly=True,
                                 compute="_document_count",
                                 help="Total number of students assigned to "
                                      "this route.")
    color = fields.Integer(string='Color Index', help="Color index for the "
                                                      "route")
    vehicle_ids = fields.One2many('edu.vehicle', 'trip_rel_id',
                                  string="Vehicle",
                                  help="Vehicles assigned to this "
                                       "route.")
    company_id = fields.Many2one('res.company', string='Company',
                                 help="Company associated with this route.",
                                 default=lambda self: self.env[
                                     'res.company']._company_default_get())
    academic_year_id = fields.Many2one('education.academic.year',
                                       string='Academic Year',
                                       help="Academic year during which this "
                                            "route is active.")

    @api.constrains('src_loc_id', 'dest_loc_id')
    def check_locations(self):
        """Ensures that the source and destination locations are not same."""
        for rec in self:
            if rec.src_loc_id == rec.dest_loc_id:
                raise ValidationError(
                    _("Source and Destination Cannot be same"))

    @api.model
    def create(self, vals):
        """Overriding the create method and assigning
                name for the newly creating record"""
        if vals['name'] == 'New':
            src_loc_id = self.env['education.stop'].browse(vals['src_loc_id'])
            dest_loc_id = self.env['education.stop'].browse(vals['dest_loc_id'])
            vals[
                'name'] = src_loc_id.stop_id.name + '-->' + dest_loc_id.stop_id.name
        res = super(EducationTrip, self).create(vals)
        return res

    def student_view(self):
        self.ensure_one()
        domain = [
            ('trip_id', '=', self.id)]
        return {
            'name': _('Students'),
            'domain': domain,
            'res_model': 'education.student',
            'type': 'ir.actions.act_window',
            'view_id': False,
            'view_mode': 'tree,form',
            'view_type': 'form',
            'context': "{'default_trip_id': '%s'}" % self.id
        }

    def _document_count(self):
        """Return the count of the students"""
        for rec in self:
            document_ids = self.env['education.student'].search(
                [('trip_id', '=', rec.id)])
            rec.total_students = len(document_ids)
