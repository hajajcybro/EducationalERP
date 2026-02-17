from odoo import http
from odoo.http import request
from odoo import fields, models


class StudentExamPortal(http.Controller):

    @http.route(['/my/exams'], type='http', auth='user', website=True)
    def portal_exam_home(self, **kwargs):
        partner = request.env.user.partner_id
        is_student = partner.is_student
        return request.render(
            'education_mobile_and_portal_access.portal_exam_home', {
                'is_student': is_student,
            }
        )

    @http.route('/my/published-exams', auth='user', website=True)
    def published_exams(self):
        partner = request.env.user.partner_id
        exams = request.env['education.exam'].sudo().search([
            ('state', '=', 'published'),
        ])
        return request.render('education_mobile_and_portal_access.portal_published_exams', {
            'exams': exams
        })

    @http.route('/my/exam-results', auth='user', website=True)
    def exam_results(self):
        partner = request.env.user.partner_id
        results = request.env['education.exam.result'].sudo().search([
            ('student_id', '=', partner.id)
        ])
        return request.render('education_mobile_and_portal_access.portal_exam_results', {
            'results': results
        })

    @http.route(['/exam/revaluation'], type='http', auth='user', website=True)
    def portal_revaluation_form(self, **kwargs):
        partner = request.env.user.partner_id
        student_class = partner.class_id
        exams = request.env['education.exam'].sudo().search([
            ('class_id', '=', student_class.id),
        ])
        return request.render('education_mobile_and_portal_access.portal_revaluation_form', {
            'exams': exams,
        })

    @http.route('/my/revaluation/submit', type='http', auth='user', website=True, csrf=True)
    def portal_revaluation_submit(self, **post):
        partner = request.env.user.partner_id
        exam_id = int(post.get('exam_id'))
        course_id = int(post.get('course_id'))
        exam = request.env['education.exam'].sudo().browse(exam_id)
        # Prevent duplicate
        existing = request.env['education.exam.revaluation'].sudo().search([
            ('student_id', '=', partner.id),
            ('exam_id', '=', exam_id),
            ('course_id', '=', course_id),
            ('state', '!=', 'cancel')
        ], limit=1)
        if existing:
            return request.render(
                'education_mobile_and_portal_access.portal_revaluation_form',
                {
                    'error_message': "Revaluation already applied for this subject and exam."
                }
            )
        # Create record
        request.env['education.exam.revaluation'].sudo().create({
            'student_id': partner.id,
            'exam_id': exam_id,
            'course_id': course_id,
            'program_id': exam.program_id.id,
            'class_id': exam.class_id.id,
            'session_id': exam.session_id.id,
            'state': 'draft',
        })
        return request.render('education_mobile_and_portal_access.application_success')



