from odoo import api, fields, models, _

class EducationalHostelFoodItem(models.Model):
    _name = 'education.hostel.food.item'
    _description = 'Hostel Food Item'

    name = fields.Char(string='Name',required=True)
