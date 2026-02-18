from odoo import http
from odoo.http import request
from .portal_utils import get_student_partner


class StudentPortalController(http.Controller):
    @http.route(['/my/profile'], type='http', auth='user', website=True)
    def portal_student_profile(self, **kwargs):
        partner = get_student_partner()
        documents = request.env['education.document'].sudo().search([
            ('student_id', '=', partner.id),('state', '=', 'approved')
        ])
        if not partner.position_role == 'student':
            return request.redirect('/my')
        return request.render('education_mobile_and_portal_access.portal_student_profile', {
            'student': partner,
            'documents': documents,
        })

    @http.route(['/my/document/update'], type='http', auth='user', website=True)
    def portal_add_document_form(self, **kwargs):
        partner = get_student_partner()
        if not partner.position_role == 'student':
            return request.redirect('/my')
        doc_types = request.env['education.document.type'].sudo().search([])
        return request.render(
            'education_mobile_and_portal_access.portal_add_document',
            {
                'doc_types': doc_types,
            }
        )

    @http.route(['/my/document/submit'],type='http', auth='user', methods=['POST'], website=True, csrf=True)
    def portal_submit_document(self, **post):
        partner = get_student_partner()
        document_type = int(post.get('document_type'))
        file = post.get('attachment')
        if file:
            request.env['education.document'].sudo().create({
                'student_id': partner.id,
                'program_id':partner.program_id.id,
                'document_type': document_type,
                'attachment': file.read(),
                'file_name': file.filename,
            })
        return request.redirect('/my/profile?message=submitted')

    @http.route(['/my/document/download/<int:doc_id>'], type='http', auth='user', website=True)
    def portal_download_document(self, doc_id, **kwargs):
        partner = get_student_partner()
        document = request.env['education.document'].sudo().search([
            ('id', '=', doc_id),
            ('student_id', '=', partner.id),
            ('state', '=', 'approved')
        ], limit=1)

        if not document or not document.attachment:
            return request.redirect('/my/profile')

        import base64
        file_data = base64.b64decode(document.attachment)
        headers = [
            ('Content-Type', 'application/octet-stream'),
            ('Content-Disposition', f'attachment; filename="{document.file_name or "document"}"'),
        ]
        return request.make_response(file_data, headers=headers)