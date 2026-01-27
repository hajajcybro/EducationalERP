from odoo import http
from odoo.http import request

class StudentPortal(http.Controller):

    @http.route(['/my/student/profile'], type='http', auth='user', website=True)
    def student_profile(self):
        partner = request.env.user.partner_id
        return request.render('education_portal.student_profile_template', {
            'student': partner
        })
