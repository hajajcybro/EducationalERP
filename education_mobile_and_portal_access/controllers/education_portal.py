from odoo.addons.portal.controllers.portal import CustomerPortal
from odoo.http import request


class CustomPortalDashboard(CustomerPortal):

    def _prepare_home_portal_values(self, counters):
        # Get default values first
        values = super()._prepare_home_portal_values(counters)
        partner = request.env.user.partner_id

        # Count unread notifications specifically for the 'Attendance' module
        unread_notifications = request.env['edu.notification'].sudo().search([
            ('module', '=', 'attendance'),
            ('status', 'in', ['pending', 'sent']),
            ('recipient_ids', 'in', partner.id),
            ('read_by_partner_ids', 'not in', partner.id)
        ])

        # Send this number to your XML
        values['unread_attendance'] = len(unread_notifications)

        # Pass the message of the most recent notification for the hover text
        if unread_notifications:
            values['attendance_message'] = unread_notifications[0].message
        else:
            values['attendance_message'] = ""

        return values
