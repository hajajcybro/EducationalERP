from odoo import models, fields

class EducationCategory(models.Model):
    _name = 'education.category'
    _description = 'Student Category'

    name = fields.Char(string='Category Name',
                    required=True,
                    help = 'Enter the name of the student category, e.g:  Merit, International.'
                   )
    description = fields.Text(string='Description',
                              required=True,
                              help='Provide additional details about this category.'
                              )
