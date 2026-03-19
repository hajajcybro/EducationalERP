from odoo import http
from odoo.http import request
from .portal_utils import get_student_partner
import base64

class StudentPortalController(http.Controller):
    @http.route(['/my/profile'], type='http', auth='user', website=True)
    def portal_student_profile(self, **kwargs):
        """
            Display the Student Profile page in the portal.
            - Retrieves the logged-in student partner record.
            - Ensures the user has position_role = 'student'.
            - Fetches approved education documents linked to the student.
            - Renders the student profile template with student
          and document details.
        """
        partner = get_student_partner()
        print(partner.read())
        if not partner.position_role == 'student':
            return request.redirect('/my')
        return request.render('education_core.portal_student_profile', {
            'student': partner,
        })

    @http.route(['/student/application'], type='http', auth='public', website=True)
    def student_application_form(self, **kwargs):
        if not request.env.user._is_public():
            return request.redirect('/my/profile')
        # Fetch available programs and academic years for the dropdown lists
        programs = request.env['education.program'].sudo().search([])
        years = request.env['education.academic.year'].sudo().search([('state', '!=', 'closed')])

        return request.render('education_core.application_form', {
            'programs': programs,
            'years': years,
        })

    # 2. Route to Handle Form Submission
    @http.route(['/student/application/submit'], type='http', auth='public', website=True, methods=['POST'], csrf=True)
    def student_application_submit(self, **post):
        # Retrieve form data and map it to your Odoo Model fields
        vals = {
            'name': post.get('name'),
            'email': post.get('email'),
            'phone': post.get('phone'),
            'dob': post.get('dob'),
            'id_no': post.get('id_no'),
            'street': post.get('street'),
            'street2': post.get('street2'),
            'city': post.get('city'),
            'program_id': int(post.get('program')) if post.get('program') else False,
            'academic_year_id': int(post.get('year')) if post.get('year') else False,
        }
        # Use sudo() because public website visitors don't have write access by default
        application = request.env['education.application'].sudo().create(vals)
        document = post.get('document')
        if document:
            request.env['ir.attachment'].sudo().create({
                'name': document.filename,
                'type': 'binary',
                'datas': base64.b64encode(document.read()),
                'res_model': 'education.application',
                'res_id': application.id,
            })
        return request.render('education_core.application_success', {})

