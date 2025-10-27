from odoo import models, api

class ResPartner(models.Model):
    _inherit = 'res.partner'


    def action_attendance(self):
        print('attendance')
