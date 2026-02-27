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
        if not partner:
            return request.redirect('/my')
        transport = request.env['education.transport.assignment'].sudo().search([
            ('student_id', '=', partner.id),('active', '=', True)
        ], limit=1)
        route = False
        stop = False
        stops = False
        if transport:
            route = transport.route_id
            stop = transport.stop_id
            stops = route.stops.sorted(key=lambda s: s.sequence)
        # transport_fee = request.env['education.fee.invoice'].sudo().search([
        #     ('student_id', '=', partner.id),
        #     ('payment_type', '=', 'transport'),
        #     ('status', '!=', 'paid'),
        # ], limit=1)
        # pending_amount = 0.0
        # if transport_fee:
        #     pending_amount = transport_fee.outstanding_amount
        return request.render(
            'education_transport.portal_transport',
            {
                'transport': transport,
                'route': route,
                'stop': stop,
                'stops': stops,
                # 'transport_fee': transport_fee,
                # 'pending_amount': pending_amount,
            }
        )


