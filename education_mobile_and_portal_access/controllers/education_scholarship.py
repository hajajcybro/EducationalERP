from odoo import http
from odoo.http import request
from .portal_utils import get_student_partner

class ScholarshipPortal(http.Controller):

    @http.route(['/my/scholarship'], type='http', auth='user', website=True)
    def portal_scholarship(self, **kwargs):
        """
           Render the Scholarship Home page in the portal.
           - Retrieves the logged-in user's partner record.
           - Passes a boolean flag to the template to control
             student-specific scholarship access and visibility.
           """
        partner = request.env.user.partner_id
        student = partner.position_role == 'student'
        unread_notifications = request.env['edu.notification'].sudo().search([
            ('module', '=', 'scholarship'),
            ('status', 'in', ['pending', 'sent']),
            ('recipient_ids', 'in', partner.id),
            ('read_by_partner_ids', 'not in', partner.id)
        ])
        alert_messages = [n.message for n in unread_notifications if n.message]
        # Mark all as read
        for notif in unread_notifications:
            notif.sudo().write({'read_by_partner_ids': [(4, partner.id)]})
        return request.render(
            'education_mobile_and_portal_access.portal_scholarship_home',
            {
                'student': student,
                'alert_messages': alert_messages,
            }
        )

    @http.route(['/my/published-scholarships'], type='http', auth='user', website=True)
    def portal_published_scholarships(self, **kwargs):
        """
           Display all open scholarships in the portal.
           - Retrieves scholarship records with status = 'open'.
           - Renders the published scholarships template
             with available scholarship listings.
           """
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
        """
           Render the Scholarship Application form page.
           - Retrieves all active and open scholarships.
           - Allows public access (auth='public').
           - Accepts an optional error message via query parameters.
           - Passes scholarship records and error message to the template.
        """
        scholarships = request.env['education.scholarship'].sudo().search([
            ('status', '=', 'open'),
            ('active', '=', True),
        ])
        error_message = kwargs.get('error')
        return request.render(
            'education_mobile_and_portal_access.portal_apply_scholarship',
            {
                'scholarships': scholarships,
                'error': error_message,  # Pass error to XML
            }
        )

    @http.route(['/scholarship/application/submit'], type='http',
                auth='user', website=True, methods=['POST'], csrf=True)
    def submit_scholarship(self, **post):
        """
            Handle submission of a Scholarship Application.
            - Retrieves the logged-in student's partner record.
            - Prevents duplicate applications for the same scholarship.
            - Creates a new education.scholarship.application record
              with bank and account details.
            - Sets the application state to 'submitted'.
            - Uploads required supporting documents dynamically
              based on scholarship document_type_ids.
            - Renders a success page upon successful submission.
            """
        partner = request.env.user.partner_id
        scholarship_id = int(post.get('scholarship_id'))
        # Prevent duplicate application
        existing = request.env['education.scholarship.application'].sudo().search([
            ('student_id', '=', partner.id),
            ('scholarship_id', '=', scholarship_id),
        ], limit=1)
        if existing:
            return self.scholarship_application(error="Scholarship already applied for this student.")

            # return request.redirect('/my/scholarship')
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
        return request.render('education_mobile_and_portal_access.application_success')

    @http.route('/my/my-scholarship', type='http', auth='user', website=True)
    def portal_my_scholarship(self, **kwargs):
        """
            Display the approved scholarship details for the student.
            - Retrieves the logged-in student partner record.
            - Redirects to '/my' if no valid student is found.
            - Fetches the latest approved scholarship application
              (state = 'approved') for the student.
            - Renders the scholarship details page with the application record.
            """
        partner = get_student_partner()
        if not partner:
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


