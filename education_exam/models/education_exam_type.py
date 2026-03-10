from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError


class EducationExamType(models.Model):
    """
           Model representing Education Exams.

       """
    _name = 'education.exam.type'
    _description = 'Education Exam Type'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    name = fields.Char(
        string='Name', help='Name of the education exam type.')
