from odoo import http
from odoo.http import request
from .portal_utils import get_student_partner


class HostelApplicationWebsite(http.Controller):

    @http.route('/hostel/application', type='http', auth='user', website=True)
    def hostel_application_form(self):
        hostels = request.env['education.hostel'].sudo().search([])
        partner = request.env.user.partner_id
        if partner.position_role != 'student':
            return request.redirect('/my')
        existing = request.env['education.hostel.application'].sudo().search([
            ('student_id', '=', partner.id),
            ('state', '!=', 'draft')
        ], limit=1)

        if existing:
            return request.redirect('/my')
        return request.render(
            'education_mobile_and_portal_access.hostel_application_form',
            {'hostels': hostels}
        )
    @http.route('/hostel/application/submit',
                type='http',
                auth='user',
                methods=['POST'],
                website=True,
                csrf=True)
    def hostel_application_submit(self, **post):
        partner = request.env.user.partner_id
        if not partner.position_role == 'student':
            return request.redirect('/my')
        request.env['education.hostel.application'].sudo().create({
            'student_id': partner.id,
            'email': partner.email,
            'phone': partner.phone,
            'mobile': partner.mobile,
            'id_no': partner.id_no,
            'program_id': partner.program_id.id,
            'class_id': partner.class_id.id,
            'hostel_id': int(post.get('hostel_id')),
            'state': 'draft',
        })
        return request.render(
            'education_mobile_and_portal_access.application_success'
        )

    @http.route(['/my/hostel'], type='http', auth='user', website=True)
    def portal_hostel(self, **kwargs):
        partner = get_student_partner()
        if not partner:
            return request.redirect('/my')

        application = request.env['education.hostel.application'].sudo().search([
            ('student_id', '=', partner.id),
            # ('state', '=', 'allocated')
        ], limit=1)
        allocation = False
        hostel = False
        room = False
        if application:
            allocation = request.env['education.hostel.room.allocation'].sudo().search([
                ('hostel_application_id', '=', application.id),
                ('vacated_date', '=', False)
            ], limit=1)
            if allocation:
                hostel = allocation.hostel_id
                room = allocation.room_id
        hostel_fee = request.env['education.fee.invoice'].sudo().search([
            ('student_id', '=', partner.id),
            ('payment_type', '=', 'hostel'),
            ('status', '!=', 'paid'),
        ], limit=1)

        pending_amount = 0.0
        if hostel_fee:
            pending_amount = hostel_fee.outstanding_amount

        return request.render(
            'education_mobile_and_portal_access.portal_hostel',
            {
                'application': application,
                'allocation': allocation,
                'hostel': hostel,
                'room': room,
                'hostel_fee': hostel_fee,
                'pending_amount': pending_amount,
                'student': partner,
            }
        )

