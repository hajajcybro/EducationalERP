from odoo import fields, models



class MessFood(models.Model):
    """Created model for handling food items in mess """
    _name = 'education.hostel.mess.food'
    _description = 'Food Order'

    morning_food_id = fields.Many2one('education.hostel.food.item', string="Breakfast",
                                    help="Select Breakfast item.")
    lunch_id = fields.Many2one('education.hostel.food.item', string="Lunch",
                               help="Lunch item.")
    snack_id = fields.Many2one('education.hostel.food.item', string="Evening Snack",
                               help="Evening snack.")
    dinner_id = fields.Many2one('education.hostel.food.item', string="Dinner",
                                help="Mention the supper item.")
    weekday = fields.Selection(
        [
            ('mon', 'Monday'),
            ('tue', 'Tuesday'),
            ('wed', 'Wednesday'),
            ('thu', 'Thursday'),
            ('fri', 'Friday'),
            ('sat', 'Saturday'),
            ('sun', 'Sunday'),
        ],
        string="Weekday",
        required=True,
        help="Select the weekday"
    )

    mess_id = fields.Many2one('education.hostel.mess', string="MESS",
                              help='Mess related to the food item')

