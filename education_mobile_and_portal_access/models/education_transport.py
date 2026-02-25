from odoo import models


class TransportDelayWizardNotification(models.TransientModel):
    """
    Inherits transport.delay.wizard to also send portal in-app notifications
    to students on the delayed route, alongside the existing parent emails.
    """
    _inherit = 'transport.delay.wizard'

    def action_send_notifications(self):
        """Override to send portal in-app notification to each student after emails."""
        res = super().action_send_notifications()
        # Fetch all active students on this route
        assignments = self.env['education.transport.assignment'].sudo().search([
            ('route_id', '=', self.route_id.id),
            ('active', '=', True)
        ])
        for assign in assignments:
            student = assign.student_id  # res.partner directly
            notif = self.env['edu.notification'].sudo().create({
                'name': f'Transport Delay: {self.route_id.name}',
                'message': (
                    f'Your transport route "{self.route_id.name}" is delayed by '
                    f'{self.delay_minutes} minute(s). '
                    f'Reason: {self.delay_reason}'
                ),
                'recipient_ids': [(4, student.id)],
                'module': 'transport',
                'notification_type': 'in_app',
                'status': 'draft',
            })
            notif.action_send()
        return res