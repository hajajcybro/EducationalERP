from odoo import models

class EduFeeInvoiceHostelNotification(models.Model):
    """
    Inherits education.fee.invoice to send a portal in-app notification
    when a hostel fee invoice is created (action_create_invoice).
    This allows the NEW badge to appear on the Hostel card and disappear
    once the student visits /my/hostel (marked as read).
    """
    _inherit = 'education.fee.invoice'

    def action_create_invoice(self):
        res = super().action_create_invoice()
        # Only notify for hostel payment type
        if self.payment_type == 'hostel' and self.student_id:
            self.env['edu.notification'].sudo().create({
                'name': f'Hostel Fee Due: {self.student_id.name}',
                'message': '',
                'recipient_ids': [(4, self.student_id.id)],
                'module': 'hostel',
                'notification_type': 'in_app',
                'status': 'draft',
            }).action_send()

        return res