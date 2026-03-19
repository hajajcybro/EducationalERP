from odoo import models, fields, api
from odoo.exceptions import ValidationError

class EducationApplicationRejectWizard(models.TransientModel):
    _name = 'education.application.reject.wizard'
    _description = 'Application Rejection Wizard'

    application_id = fields.Many2one('education.application', required=True)
    reject_reason = fields.Text('Rejection Reason', required=True)

    def action_confirm_reject(self):
        """Update application state and reason"""
        self.ensure_one()
        self.application_id.write({
            'state': 'rejected',
            'reject_reason': self.reject_reason,
        })
        return {'type': 'ir.actions.act_window_close'}


