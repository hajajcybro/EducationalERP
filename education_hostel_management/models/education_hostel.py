# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
import re


class EducationHostel(models.Model):
    _name = 'education.hostel'
    _description = 'Hostel'
    _inherit = ['mail.thread', 'mail.activity.mixin']


    name = fields.Char( string='Hostel Name',required=True,help='Hostel Name')
    hostel_code = fields.Char(string='Hostel Code',required=True,help='Hostel Code')
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        required=True,
        default=lambda self: self.env.company.currency_id
    )

    # address fields
    street = fields.Char(string='Street', help='Hostel Street')
    street2 = fields.Char(string='Street2', help='Hostel Street2')
    zip = fields.Char(string='Zip Code',change_default=True,help='Zip Code')
    city = fields.Char(string='City', help='City of hostel')
    state_id = fields.Many2one("res.country.state", string='State', ondelete='restrict',
                                                domain="[('country_id', '=?', country_id)]")
    country_id = fields.Many2one('res.country', string='Country', ondelete='restrict')
    country_code = fields.Char(related='country_id.code', string="Country Code")
    email = fields.Char(string='Email', help='Email Id of hostel',required=True)
    phone = fields.Char(string='Phone', required=True, help='Phone Number')
    mobile = fields.Char(string='Mobile', required=True, help='Mobile Number')

    total_floors = fields.Integer(string='Total Floors' , help='Total Floors in the hostel.')
    total_rooms = fields.Integer(string='Total Rooms' ,  compute="_compute_student_total",
                              help="Total Rooms inside hostel.")
    capacity = fields.Char(string="Capacity",required=True, compute="_compute_student_total",
                                  help="Capacity of the hostel.")

    warden_id = fields.Many2one('hr.employee',
                                       required=True, string="Warden",
                                       help="Warden of the hostel.")
    room_rent = fields.Monetary(string="Room Rent",  currency_field='currency_id', required=True, tracking=1,
                            help="Room rent of the hostel.")
    mess_fee = fields.Monetary(string="Mess Fee", currency_field='currency_id', required=True, tracking=1,
                           help="Mess fee.")
    vacancy = fields.Char(string="Vacancy",
                          compute="_compute_student_total",
                          help="Vacancy of the hostel.")
    total_fee = fields.Monetary(string="Total Fee", compute="_compute_total_fee",
                        help="Total fee.")
    total_students = fields.Integer(string="Students",
                                 compute="_compute_student_total",
                                 help="Total students of the hostel.")
    hostel_room_ids = fields.One2many('education.room.list',
                                      'hostel_room_rel2',
                                      string="Rooms",
                                      help="Hostel rooms.")





    @api.depends('room_rent', 'mess_fee')
    def _compute_total_fee(self):
        for rec in self:
            rec.total_fee = (rec.room_rent or 0.0) + (rec.mess_fee or 0.0)

    def action_view_hostel_student(self):
        """Shows the students in the hostel"""
        self.ensure_one()
        domain = [
            ('hostel_id', '=', self.id),
            ('state', '=', 'allocated'),
            ('vacated_date', '=', False)]
        return {
            'name': _('Students'),
            'domain': domain,
            'res_model': 'res.partner)',
            'type': 'ir.actions.act_window',
            'view_id': False,
            'view_mode': 'list,form',
            'view_type': 'tree',
            'context': "{'default_room': '%s'}" % self.id
        }

    @api.constrains('email', 'phone', 'mobile', )
    def _check_contact_fields(self):
        """Validate email and phone formats."""
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        phone_pattern = r'^\+?\d{7,15}$'

        for record in self:
            if record.email and not re.match(email_pattern, record.email):
                raise ValidationError(_('Invalid email address. Please enter a valid format like name@example.com.'))

            phone_fields = {
                'Phone': record.phone,
                'Mobile': record.mobile,
            }
            for field_label, value in phone_fields.items():
                if value and not re.match(phone_pattern, value):
                    raise ValidationError(_(
                        'Invalid %s. Please enter digits only (7–15 numbers) with optional + sign.'
                    ) % field_label)


    def _compute_student_total(self):
        """Compute the vacancy,total students and hostel capacity"""
        for rec in self:
            rec.total_rooms = len(rec.hostel_room_ids)
            total_vacancy = 0
            allocated = 0
            capacity = 0
            for data in rec.hostel_room_ids:
                allocated += int(data.room_mem_rel.allocated_no)
                capacity += int(data.room_mem_rel.capacity)
                total_vacancy += int(data.room_mem_rel.vacancy)
            rec.capacity = capacity
            rec.total_students = allocated
            rec.vacancy = total_vacancy
            if rec.capacity:
                rec.vacancy = capacity - allocated
