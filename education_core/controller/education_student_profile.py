from odoo import http
from odoo.http import request
from .portal_utils import get_student_partner


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