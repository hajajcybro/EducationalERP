
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class EducationHostelRoom(models.Model):
    """Creating a model for rooms in hostel"""
    _name = 'education.hostel.room'
    _rec_name = 'room_no'
    _description = "Room"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    room_no = fields.Char(string='Room Number',required=True)
    hostel_id = fields.Many2one(
        'education.hostel', string='Hostel', required=True,ondelete='cascade')

    capacity = fields.Integer(string='Capacity')
    vacancy = fields.Integer(string='Vacancy',readonly=1)
    allocated_no = fields.Integer(string='Allocated Number',readonly=1)

    gender = fields.Selection(selection=[('male', 'Male'),('female', 'Female'), ('other', 'Other'),],
                              string='Allowed Gender')

    floor_id = fields.Many2one('education.hostel.floor',string='Floor',help='Floor where the room is located',required=True)

    status = fields.Selection(selection=[
            ('available', 'Available'), ('full', 'Full'),
            ('maintenance', 'Under Maintenance'), ],
        string='Status',default='available',required=True
    )


    @api.onchange('allocated_no')
    def _onchange_allocated_no(self):
        if self.allocated_no == self.capacity and  self.capacity !=0:
            print("jjjjjjjjjjjjjj")
            self.status = 'full'

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('capacity'):
                vals['vacancy'] = vals['capacity']
                vals['allocated_no'] = 0

        records = super().create(vals_list)

        for record in records:
            self.env['education.room.list'].create({
                'room_mem_rel': record.id,
                'floor': record.floor_id.id,
            })

        return records


