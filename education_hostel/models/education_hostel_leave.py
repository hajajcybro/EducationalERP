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
import math
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class EducationHostelLeave(models.Model):
    """Creates the model education.hostel_leave"""
    _name = 'education.hostel_leave'
    _description = "Leave Request"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    request_id = fields.Char(string='Request ID', required=True, copy=False,
                             readonly=True,
                             index=True, default=lambda self: _('New'),
                             help="Request ID of the hostel leave")
    name = fields.Many2one('education.host_std', string="Member", required=True,
                           help="Name of the hostel leave")
    hostel = fields.Many2one('education.hostel', string="Hostel",
                             related='name.hostel', help="Name of the hostel")
    leave_from = fields.Datetime(string="Date From", required=True,
                                 help="Specify the starting date for the leave")
    leave_to = fields.Datetime(string="Date To", required=True,
                               help="Specify the ending date for the leave "
                                    "request.")
    reason = fields.Text(String="Reason", required=True,
                         help="Reason for leave request")
    number_of_days = fields.Float('Number of Days',
                                  compute='_compute_number_of_days', store=True,
                                  track_visibility='onchange',
                                  readonly=True,
                                  help="Number of days of the leave")
    company_id = fields.Many2one('res.company', string='Company',
                                 default=lambda self: self.env.company.id)
    state = fields.Selection([
        ('draft', 'To Submit'),
        ('cancel', 'Cancelled'),
        ('confirm', 'To Approve'),
        ('refuse', 'Refused'),
        ('validate', 'Approved')
    ], string='Status', readonly=True, track_visibility='onchange', copy=False,
        default='confirm',
        help="The status is set to 'To Submit', when a leave request is created." +
             "\nThe status is 'To Approve', when leave request is confirmed by user." +
             "\nThe status is 'Refused', when leave request is refused by manager." +
             "\nThe status is 'Approved', when leave request is approved by manager.")

    @api.depends('leave_from', 'leave_to')
    def _compute_number_of_days(self):
        """compute the total leave days"""
        for holiday in self:
            if holiday.leave_from and holiday.leave_to:
                from_dt = fields.Datetime.from_string(holiday.leave_from)
                to_dt = fields.Datetime.from_string(holiday.leave_to)
                time_delta = to_dt - from_dt
                holiday.number_of_days = math.ceil(
                    time_delta.days + float(time_delta.seconds) / 86400)

    def action_confirm(self):
        """confirm the leave request"""
        return self.write({'state': 'confirm'})

    def action_validate(self):
        """validate the leave request"""
        for holiday in self:
            holiday.write({'state': 'validate'})

    def action_refuse(self):
        """refuse the leave request"""
        for holiday in self:
            holiday.write({'state': 'cancel'})

    @api.constrains('leave_from', 'leave_to')
    def check_dates(self):
        """Method check_dates to check the date"""
        for rec in self:
            if rec.leave_from >= rec.leave_to:
                raise ValidationError(
                    _('From date must be anterior to To date'))

    @api.model
    def create(self, vals):
        """Overriding the create method and assigning the the request id
        for the record"""
        if vals.get('request_id', _('New')) == _('New'):
            vals['request_id'] = self.env['ir.sequence'].next_by_code(
                'hostel.leave') or _('New')
        return super(EducationHostelLeave
                     , self).create(vals)
