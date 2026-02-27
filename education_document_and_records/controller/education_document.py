from odoo import http
from odoo.http import request
from .portal_utils import get_student_partner


class StudentPortalController(http.Controller):
    @http.route(['/my/document'], type='http', auth='user', website=True)
    def portal_student_document(self, **kwargs):
        """
                Display the Student Profile page in the portal.
                - Retrieves the logged-in student partner record.
                - Ensures the user has position_role = 'student'.
                - Fetches approved education documents linked to the student.
                - Renders the student profile template with student
                  and document details.
        """
        partner = get_student_partner()
        documents = request.env['education.document'].sudo().search([
            ('student_id', '=', partner.id),('state', '=', 'approved')
        ])
        # unread_notifications = request.env['edu.notification'].sudo().search([
        #     ('module', '=', 'document'),
        #     ('status', 'in', ['pending', 'sent']),
        #     ('recipient_ids', 'in', partner.id),
        #     ('read_by_partner_ids', 'not in', partner.id)
        # ])
        # alert_messages = [n.message for n in unread_notifications if n.message]
        # # Mark all as read
        # for notif in unread_notifications:
        #     notif.sudo().write({'read_by_partner_ids': [(4, partner.id)]})

        if not partner.position_role == 'student':
            return request.redirect('/my')
        return request.render('education_document_and_records.portal_student_document', {
            'student': partner,
            'documents': documents,
        })

    @http.route(['/my/document/update'], type='http', auth='user', website=True)
    def portal_add_document_form(self, **kwargs):
        """
            Render the Add Document form in the student portal.
            - Validates that the logged-in user is a student.
            - Retrieves available document types.
            - Renders the document upload form template.
        """
        partner = get_student_partner()
        if not partner.position_role == 'student':
            return request.redirect('/my')
        doc_types = request.env['education.document.type'].sudo().search([])
        return request.render(
            'education_document_and_records.portal_add_document',
            {
                'doc_types': doc_types,
            }
        )

    @http.route(['/my/document/submit'],type='http', auth='user', methods=['POST'], website=True, csrf=True)
    def portal_submit_document(self, **post):
        """
            Handle submission of a student document.
            - Retrieves the logged-in student partner record.
            - Accepts uploaded file and selected document type.
            - Creates a new education.document record.
            - Associates the document with the student and program.
            - Redirects to the profile page with a submission message.
        """
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
        return request.redirect('/my/document?message=submitted')

    @http.route(['/my/document/download/<int:doc_id>'], type='http', auth='user', website=True)
    def portal_download_document(self, doc_id, **kwargs):
        """
            Download an approved student document.
            - Retrieves the logged-in student partner record.
            - Ensures the requested document:
                * Belongs to the student.
                * Is in 'approved' state.
                * Contains attachment data.
            - Decodes the stored base64 file.
            - Returns the file as a downloadable HTTP response.
            - Redirects to profile if validation fails.
        """
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