from odoo import models, fields, api


class EducationLibraryReservationNotification(models.Model):
    """
    Inherits education.library.reservation to send portal in-app notifications.
    Triggers:
    - status -> 'available': Book is ready to collect
    """
    _inherit = 'education.library.reservation'

    def action_mark_available(self, expiry_hours=None):
        """
        Override action_mark_available.
        After book becomes available, notify the member via portal notification.
        """
        res = super().action_mark_available(expiry_hours=expiry_hours)

        partner = self.member_id.partner_id
        if partner:
            notif = self.env['edu.notification'].sudo().create({
                'name': f'Book Available: {self.book_id.title}',
                'message': (
                    f'Your reserved book "{self.book_id.title}" is now available for collection. '
                    f'Please collect it before {self.expiry_date}.'
                ),
                'recipient_ids': [(4, partner.id)],
                'module': 'library',
                'notification_type': 'in_app',
                'status': 'draft',
            })
            notif.action_send()

        return res

    def _send_overdue_notification(self):
        """
        Override to also send portal in-app notification alongside email.
        Fires from cron: _cron_send_overdue_notifications (newly overdue).
        """
        res = super()._send_overdue_notification()

        partner = self.member_id.partner_id
        if partner:
            notif = self.env['edu.notification'].sudo().create({
                'name': f'Book Overdue: {self.book_id.title}',
                'message': (
                    f'Your book "{self.book_id.title}" is overdue by {self.days_overdue} day(s). '
                    f'A fine of ₹{self.fine_amount} has been applied. Please return it immediately.'
                ),
                'recipient_ids': [(4, partner.id)],
                'module': 'library',
                'notification_type': 'in_app',
                'status': 'draft',
            })
            notif.action_send()

        return res

    def action_return_book(self):
        """
        Override action_return_book.
        After return, if a fine was generated, notify the member.
        """
        res = super().action_return_book()

        # Notify only if there is a fine
        if self.fine_amount > 0:
            partner = self.member_id.partner_id
            if partner:
                notif = self.env['edu.notification'].sudo().create({
                    'name': f'Library Fine: {self.book_id.title}',
                    'message': (
                        f'You have a fine of ₹{self.fine_amount} for the late return of '
                        f'"{self.book_id.title}" ({self.days_overdue} day(s) overdue). '
                        f'Please check the History section for details.'
                    ),
                    'recipient_ids': [(4, partner.id)],
                    'module': 'library',
                    'notification_type': 'in_app',
                    'status': 'draft',
                })
                notif.action_send()

        return res