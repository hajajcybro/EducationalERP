from odoo import models, api

class EducationEnrollment(models.Model):
    _inherit = 'education.enrollment'


    @api.model
    def action_attendance(self):
        print('attendance')
