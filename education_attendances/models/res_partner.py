from odoo import models, fields,api
from odoo.exceptions import ValidationError


class ResPartner(models.Model):
    _inherit = 'res.partner'

    last_attendance_mail_date = fields.Date(
        string="Last Attendance Notification Date"
    )

    def action_attendance(self):
        """Open attendance related to this student."""
        self.ensure_one()
        enrollment = self.env['education.enrollment'].search([
            ('student_id', '=', self.id)
        ], limit=1)

        return {
            'type': 'ir.actions.act_window',
            'name': f'Attendance - {self.name}',
            'res_model': 'education.attendance',
            'view_mode': 'list,form',
            'domain': [('student_id', '=', self.id)],
            'context': {'default_student_id': enrollment.id if enrollment else False}
        }


