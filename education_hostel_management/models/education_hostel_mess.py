from odoo import fields, models


class EducationHostelMess(models.Model):
    """Create model education.hostel.mess for handling mess '"""
    _name = 'education.hostel.mess'
    _description = "Mess"

    name = fields.Char(string="Name", required="True",
                            help="Mess name.")
    mess_code = fields.Char(string="Code", required="True",
                            help='Code of mess')
    hostel_id = fields.Many2one('education.hostel', string="Hostel",
                                required="True", help="Hostel.")
    hostel_food_menu_ids = fields.One2many('education.hostel.mess.food', 'mess_id',
                                    string="Food Menu", help="Menu list")
