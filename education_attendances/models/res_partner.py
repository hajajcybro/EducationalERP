from odoo import models, api
from odoo.exceptions import ValidationError


class ResPartner(models.Model):
    _inherit = 'res.partner'

    def action_attendance(self):
        """Open attendance related to this student."""
        self.ensure_one()
        enrollment = self.env['education.enrollment'].search([
            ('student_id', '=', self.id)
        ], limit=1)

        # domain = [('student_id', '=', enrollment.id)] if enrollment else [('id', '=', False)]
        return {
            'type': 'ir.actions.act_window',
            'name': f'Attendance - {self.name}',
            'res_model': 'education.attendance.summary',
            'view_mode': 'list,form',
            'domain': [('student_id', '=', self.id)],
            'context': {'default_student_id': enrollment.id if enrollment else False}
        }


