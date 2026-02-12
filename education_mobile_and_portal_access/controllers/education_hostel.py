from odoo import http
from odoo.http import request


class HostelApplicationWebsite(http.Controller):

    @http.route('/hostel/application', type='http', auth='user', website=True)
    def hostel_application_form(self):
        hostels = request.env['education.hostel'].sudo().search([])
        partner = request.env.user.partner_id
        if not partner.is_student:
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
        if not partner.is_student:
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
