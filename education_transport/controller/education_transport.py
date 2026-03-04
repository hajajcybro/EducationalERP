from odoo import http
from odoo.http import request
from .portal_utils import get_student_partner

class TransportExamPortal(http.Controller):

    @http.route(['/my/transport'], type='http', auth='user', website=True)
    def portal_transport(self, **kwargs):
        """
            Display the student's transport details in the portal.
            - Retrieves the logged-in student partner record.
            - Fetches the active education.transport.assignment record.
            - Retrieves assigned route and stop details.
            - Sorts all route stops by sequence for structured route plan display.
            - Fetches unpaid transport fee invoices.
            - Calculates pending transport amount (if any).
            - Renders the transport portal template with all related data.
        """
        partner = get_student_partner()
        transport = False
        route = False
        stop = False
        stops = False
        if partner:
            transport = request.env['education.transport.assignment'].sudo().search([
                ('student_id', '=', partner.id),('active', '=', True)
            ], limit=1)
            if transport:
                route = transport.route_id
                stop = transport.stop_id
                stops = route.stops.sorted(key=lambda s: s.sequence)
            # Fetch unread transport notifications for this student
            notifications = request.env['edu.notification'].sudo().search([
                ('module', '=', 'transport'),
                ('status', 'in', ['pending', 'sent']),
                ('recipient_ids', 'in', partner.id),
                ('read_by_partner_ids', 'not in', partner.id),
            ])
            # Mark them as read now that the student is viewing the page
            for notif in notifications:
                notif.sudo().write({
                    'read_by_partner_ids': [(4, partner.id)]
                })
            alert_messages = notifications.mapped('message')
        return request.render(
            'education_transport.portal_transport',
            {
                'transport': transport,
                'route': route,
                'stop': stop,
                'stops': stops,
                'alert_messages': alert_messages,
                'is_student': bool(partner),
            }
        )


