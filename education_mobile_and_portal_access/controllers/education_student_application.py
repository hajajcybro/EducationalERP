from odoo import http
from odoo.http import request

class StudentApplicationWebsite(http.Controller):

    @http.route('/student/application', type='http', auth='public', website=True)
    def student_application_form(self):
        """
            Render the Student Application form page.
            - Allows public access to the admission form.
            - Redirects portal users (already logged-in students/parents)
              to '/my' to prevent duplicate applications.
            - Fetches available education programs.
            - Fetches academic years.
            - Renders the application form template with required data.
        """
        if request.env.user.has_group('base.group_portal'):
            # Redirect them away or show an error
            return request.redirect('/my')
        programs = request.env['education.program'].sudo().search([])
        years = request.env['education.academic.year'].sudo().search([])
        return request.render('education_mobile_and_portal_access.application_form', {
            'programs': programs,
            'years': years
        })

    @http.route('/student/application/submit', type='http', auth='public', methods=['POST'], website=True, csrf=True)
    def submit_application(self, **post):
        """
            Handle submission of the Student Application form.
            - Accepts POST form data from the public website.
            - Creates a new education.application record.
            - Stores personal, contact, program, and academic year details.
            - Sets the initial state to 'application'.
            - Renders a success confirmation page after submission.
        """
        request.env['education.application'].sudo().create({
            'name': post.get('name'),
            'email': post.get('email'),
            'phone': post.get('phone'),
            'dob': post.get('dob'),
            'id_no': post.get('id_no') or '',
            'street': post.get('address'),
            'street2': post.get('street2') or '',
            'program_id': post.get('program'),
            'academic_year_id': post.get('year'),
            'state': 'application',
        })
        return request.render('education_mobile_and_portal_access.application_success')
