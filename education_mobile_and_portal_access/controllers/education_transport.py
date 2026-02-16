from odoo import http
from odoo.http import request


class TransportExamPortal(http.Controller):


    @http.route(['/my/transport'], type='http', auth='user', website=True)
    def portal_transport(self, **kwargs):
        partner = request.env.user.partner_id

        if not partner.is_student:
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

        # Transport Payment (IMPORTANT)
        transport_fee = request.env['education.fee.invoice'].sudo().search([
            ('student_id', '=', partner.id),
            ('payment_type', '=', 'transport'),
            ('status', '!=', 'paid'),
        ], limit=1)

        pending_amount = 0.0
        if transport_fee:
            pending_amount = transport_fee.outstanding_amount

        return request.render(
            'education_mobile_and_portal_access.portal_transport',
            {
                'transport': transport,
                'route': route,
                'stop': stop,
                'stops': stops,
                'transport_fee': transport_fee,
                'pending_amount': pending_amount,
            }
        )


