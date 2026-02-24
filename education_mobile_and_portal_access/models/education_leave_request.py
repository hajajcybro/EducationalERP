from odoo import models, api

class EducationLeaveRequestInherit(models.Model):
    # This refers to the model name inside your Leave module
    _inherit = 'education.leave.request'

    def write(self, vals):
        res = super().write(vals)
        if 'status' in vals and vals['status'] in ['approved', 'rejected']:
            for rec in self:
                if rec.student_id:
                    status_text = "Approved" if vals['status'] == 'approved' else "Rejected"

                    # We are calling 'edu.notification' from the Notification module
                    notif = self.env['edu.notification'].sudo().create({
                        'name': f'Leave {status_text}',
                        'message': f'Your leave request for {rec.start_date} was {status_text.lower()}.',
                        'recipient_ids': [(4, rec.student_id.id)],
                        'module': 'attendance',
                        'notification_type': 'in_app',
                        'status': 'draft'
                    })
                    notif.action_send()  # Triggers the send function in your notification module
        return res
