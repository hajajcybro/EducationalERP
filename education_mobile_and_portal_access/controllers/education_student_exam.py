from odoo import http
from odoo.http import request

class StudentExamPortal(http.Controller):

    @http.route('/my/published-exams', auth='user', website=True)
    def published_exams(self):
        partner = request.env.user.partner_id
        if not partner:
            return request.render('portal.portal_my_home')
        exams = request.env['education.exam'].sudo().search([
            ('state', '=', 'published')
        ])
        return request.render('education_mobile_and_portal_access.portal_published_exams', {
            'exams': exams
        })

    @http.route('/my/exam-results', auth='user', website=True)
    def exam_results(self):
        partner = request.env.user.partner_id
        if not partner:
            return request.render('portal.portal_my_home')
        results = request.env['education.exam.result'].sudo().search([
            ('student_id', '=', partner.id)
        ])
        return request.render('education_mobile_and_portal_access.portal_exam_results', {
            'results': results
        })
