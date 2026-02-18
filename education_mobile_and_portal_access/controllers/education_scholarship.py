from odoo import http
from odoo.http import request

class ScholarshipPortal(http.Controller):

    @http.route(['/my/scholarship'], type='http', auth='user', website=True)
    def portal_scholarship(self, **kwargs):
        partner = request.env.user.partner_id
        student = partner.position_role == 'student'
        return request.render(
            'education_mobile_and_portal_access.portal_scholarship_home',
            {
                'student': student,
            }
        )

    @http.route(['/my/published-scholarships'], type='http', auth='user', website=True)
    def portal_published_scholarships(self, **kwargs):
        scholarships = request.env['education.scholarship'].sudo().search([
            ('status', '=', 'open')
        ])
        return request.render(
            'education_mobile_and_portal_access.portal_published_scholarships',
            {
                'scholarships': scholarships,
            }
        )

    @http.route(['/scholarship/application'], type='http', auth='public', website=True)
    def scholarship_application(self, **kwargs):
        partner = request.env.user.partner_id
        scholarships = request.env['education.scholarship'].sudo().search([
            ('status', '=', 'open'),
            ('active', '=', True),
        ])
        return request.render(
            'education_mobile_and_portal_access.portal_apply_scholarship',
            {
                'scholarships': scholarships,
            }
        )

    @http.route(['/scholarship/application/submit'], type='http',
                auth='user', website=True, methods=['POST'], csrf=True)
    def submit_scholarship(self, **post):
        partner = request.env.user.partner_id
        scholarship_id = int(post.get('scholarship_id'))
        # Prevent duplicate application
        existing = request.env['education.scholarship.application'].sudo().search([
            ('student_id', '=', partner.id),
            ('scholarship_id', '=', scholarship_id),
        ], limit=1)
        if existing:
            return request.redirect('/my/scholarship')
        scholarship = request.env['education.scholarship'].sudo().browse(scholarship_id)
        application = request.env['education.scholarship.application'].sudo().create({
            'scholarship_id': scholarship_id,
            'student_id': partner.id,
            'bank_name': post.get('bank_name'),
            'bank_branch': post.get('bank_branch'),
            'account_holder_name': post.get('account_holder_name'),
            'bank_account_number': post.get('bank_account_number'),
            'account_type': post.get('account_type'),
            'ifsc_code': post.get('ifsc_code'),
            'swift_code': post.get('swift_code'),
            'bank_address': post.get('bank_address'),
            'state': 'submitted',
        })

        # Handle Document Upload
        for doc_type in scholarship.document_type_ids:
            file_key = f'document_{doc_type.id}'
            uploaded_file = request.httprequest.files.get(file_key)

            if uploaded_file:
                request.env['education.document'].sudo().create({
                    'student_id': partner.id,
                    'name': doc_type.name,
                    'file': uploaded_file.read(),
                })
        return request.redirect('/application_success')

    @http.route('/my/my-scholarship', type='http', auth='user', website=True)
    def portal_my_scholarship(self, **kwargs):

        partner = request.env.user.partner_id

        if not partner.position_role == 'student':
            return request.redirect('/my')

        application = request.env['education.scholarship.application'].sudo().search([
            ('student_id', '=', partner.id),
            ('state', '=', 'approved')
        ], order='id desc', limit=1)

        return request.render(
            'education_mobile_and_portal_access.portal_my_scholarship',
            {
                'application': application,
            }
        )


