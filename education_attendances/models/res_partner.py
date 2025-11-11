from odoo import models, api

class ResPartner(models.Model):
    _inherit = 'res.partner'

    def action_attendance(self):
        print('attendance')
        """Open attendance related to this student."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Documents',
            'res_model': 'education.attendance',
            'view_mode': 'list,form',
        }