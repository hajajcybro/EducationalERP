from odoo import models, fields, api
from odoo.exceptions import ValidationError

class EducationCategory(models.Model):
    _name = 'education.category'
    _description = 'Student Category'

    name = fields.Char(string='Category Name',
                    required=True,
                    help = 'Enter the name of the student category, e.g., Hostel Student, Day Scholar.'
                   )
    description = fields.Text(string='Description',
                              required=True,
                              help='Provide additional details about this category.'
                              )
