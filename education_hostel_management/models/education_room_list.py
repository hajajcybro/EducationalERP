from odoo import fields, models


class EducationRoomList(models.Model):
    """Creating model 'education.room_list'"""
    _name = 'education.room.list'
    _description = "Education Room List"

    room_mem_rel = fields.Many2one('education.hostel.room', string="Room",
                                   help='Room corresponding to the list')
    floor = fields.Many2one('education.hostel.floor', string="Floor",
                            related='room_mem_rel.floor_id',
                            help='Floor corresponding to the list')
    hostel_room_rel2 = fields.Many2one('education.hostel', string="Room",
                                       related='room_mem_rel.hostel_id',
                                       help='Hostel corresponding to the list')
