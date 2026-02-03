from odoo import http
from odoo.http import request


class HostelApplicationWebsite(http.Controller):

    @http.route('/hostel/application', type='http', auth='public', website=True)
    def hostel_application_form(self):
        hostels = request.env['education.hostel'].sudo().search([])
        return request.render(
            'education_mobile_and_portal_access.hostel_application_form',
            {'hostels': hostels}
        )
    @http.route('/hostel/application/submit',
                type='http',
                auth='public',
                methods=['POST'],
                website=True,
                csrf=True)
    def hostel_application_submit(self, **post):
        request.env['education.hostel.application'].sudo().create({
            'name': post.get('name'),
            'hostel_id': post.get('hostel_id'),
            'room_type': post.get('room_type'),
            'email': post.get('email'),
            'mobile': post.get('mobile'),
            'remarks': post.get('remarks'),
            'state': 'submitted',
        })
        return request.render(
            'education_mobile_and_portal_access.application_success'
        )
