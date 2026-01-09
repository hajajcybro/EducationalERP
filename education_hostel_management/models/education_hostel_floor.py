from odoo import api, fields, models, _


class EducationFloor(models.Model):
    """Model for handling Floor Details """
    _name = 'education.hostel.floor'
    _rec_name = "floor_no"
    _description = "Floor"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    floor_no = fields.Char(string="Floor", required=True,
                           help="Name of the floor.")
    hostel_id = fields.Many2one('education.hostel', required=True,
                                string="Hostel", help="Specify the hostel.")
    responsible_id = fields.Many2one('hr.employee',
                                     string="Responsible Staff",
                                     help="Responsible faculty of the floor.")
