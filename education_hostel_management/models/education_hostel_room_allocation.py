from odoo import api, fields, models,_
from odoo.exceptions import ValidationError


class EducationRoomAllocation(models.Model):
    """Creating model 'education.room_member'"""
    _name = 'education.hostel.room.allocation'
    _description = "Room Allocation"

    room_id = fields.Many2one('education.hostel.room',
                              string="Room",required=True, help='Room Number')
    allocated_date = fields.Date(string="Allocated Date",
                                 help='Date of allocation',
                                 default=fields.Date.today)
    vacated_date = fields.Date(string="Vacated Date",
                               help='Date of vacating room')
    floor_id = fields.Many2one('education.hostel.floor', string="Floor",

                            help='Floor corresponding to the room member')
    hostel_id = fields.Many2one('education.hostel',
                                      string="Hostel",
                                      related='room_id.hostel_id',
                                      help='Hostel of room member')

    state = fields.Selection(
        [('draft', 'Draft'), ('allocated', 'Allocated'),
         ('Vacated', 'Vacated')], default='draft', help='State of Room Allocation.')
    hostel_application_id = fields.Many2one('education.hostel.application',string='Application',
                                     help='Application for room')

    @api.constrains('allocated_date', 'vacated_date')
    def _check_allocated_date(self):
        """Validation for date"""
        for rec in self:
            if rec.allocated_date and rec.vacated_date:
                if rec.vacated_date < rec.allocated_date:
                    raise ValidationError(
                        "Vacated date cannot be earlier than allocated date")

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            application_id = vals.get('hostel_application_id')
            if application_id:
                existing_alloc = self.search_count([
                    ('hostel_application_id', '=', application_id),
                    ('vacated_date', '=', False),
                ])
                if existing_alloc:
                    raise ValidationError(_(
                        "This application already has an active room allocation. "
                        "Please vacate the current room before allocating a new one."
                    ))

            if vals.get('room_id'):
                room = self.env['education.hostel.room'].browse(vals['room_id'])
                if room.allocated_no >= room.capacity:
                    raise ValidationError(_("Selected room is already full."))

                room.write({
                    'allocated_no': room.allocated_no + 1,
                    'vacancy': room.capacity - (room.allocated_no + 1),
                })

        return super().create(vals_list)

    @api.constrains('vacated_date')
    def _check_vacated_date(self):
        for rec in self:
            if rec.vacated_date:
                rec.room_id.vacancy += 1
                rec.room_id.allocated_no -= 1

