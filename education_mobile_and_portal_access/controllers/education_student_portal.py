from odoo import http
from odoo.http import request


class StudentProfilePortal(http.Controller):

    @http.route(['/my/student/profile'], type='http', auth='user', website=True)
    def student_profile(self):
        partner = request.env.user.partner_id
        if not partner.is_student:
            return request.redirect('/my')

        return request.render(
            'education_mobile_and_portal_access.student_profile_template',
            {'partner': partner}
        )
