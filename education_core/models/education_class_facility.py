from odoo import models, fields, api

class EducationClassFacility(models.Model):
    _name = 'education.class.facility'
    _description = 'Classroom Facility'

    name = fields.Char(
        string='Facility Name',
        required=True,
        help ='Enter the name of the facility available in classrooms, such as Projector,Smart Board.'
        )
    active = fields.Boolean(
        default=True
    )
    description = fields.Text()