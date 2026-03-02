from odoo import http
from odoo.http import request
from odoo import fields, models
from .portal_utils import get_student_partner

class StudentExamPortal(http.Controller):

    @http.route(['/my/exams'], type='http', auth='user', website=True)
    def portal_exam_home(self, **kwargs):
        """
           Render the Exam Home page in the portal.
           - Retrieves the logged-in user's partner record.
           - Fetches the corresponding student partner (if applicable).
           """
        partner = request.env.user.partner_id
        student = get_student_partner()
        user_role = partner.position_role
        unread_notifications = request.env['edu.notification'].sudo().search([
            ('module', '=', 'exam'),
            ('status', 'in', ['pending', 'sent']),
            ('recipient_ids', 'in', partner.id),
            ('read_by_partner_ids', 'not in', partner.id)
        ])

        alert_messages = [n.message for n in unread_notifications if n.message]

        # Mark all as read
        for notif in unread_notifications:
            notif.sudo().write({'read_by_partner_ids': [(4, partner.id)]})

        return request.render(
            'education_exam.portal_exam_home', {
                'student': student,
                'user_role': user_role,
                'alert_messages': alert_messages,
            }
        )

    @http.route('/my/published-exams', auth='user', website=True)
    def published_exams(self):
        """
            Display all published exams in the portal.
            - Retrieves exams with state = 'published'.
            - Renders the published exams template with the exam list.
            """
        exams = request.env['education.exam'].sudo().search([
            ('state', '=', 'published'),
        ])
        return request.render('education_exam.portal_published_exams', {
            'exams': exams
        })

    @http.route('/my/exam-results', auth='user', website=True)
    def exam_results(self):
        """
            Display the logged-in student's exam results.
            - Retrieves the student partner record.
            - Fetches exam results linked to the student.
            - Renders the exam results template with result records.
            """
        student = get_student_partner()
        results = request.env['education.exam.result'].sudo().search([
            ('student_id', '=', student.id)
        ])
        print(results)
        return request.render('education_exam.portal_exam_results', {
            'results': results
        })

    @http.route(['/exam/revaluation'], type='http', auth='user', website=True)
    def portal_revaluation_form(self, **kwargs):
        """
           Render the Revaluation Application form in the portal.
           - Retrieves the logged-in user's class.
           - Filters exams based on the student's class.
           - Displays the revaluation form with available exams.
           """
        partner = request.env.user.partner_id
        student_class = partner.class_id
        exams = request.env['education.exam'].sudo().search([
            ('class_id', '=', student_class.id),
        ])
        return request.render('education_exam.portal_revaluation_form', {
            'exams': exams,
        })

    @http.route('/my/revaluation/submit', type='http', auth='user', website=True, csrf=True)
    def portal_revaluation_submit(self, **post):
        """
            Handle submission of a Revaluation Application from the portal.
            - Retrieves the selected exam and course from form data.
            - Validates that no active revaluation request already exists
              for the same student, exam, and subject.
            - Creates a new education.exam.revaluation record in 'draft' state.
            - Auto-populates program, class, and session from the selected exam.
            - Displays a success page after submission.
            - If duplicate exists, re-renders the form with an error message.
            """
        partner = request.env.user.partner_id
        exam_id = int(post.get('exam_id'))
        course_id = int(post.get('course_id'))
        exam = request.env['education.exam'].sudo().browse(exam_id)
        existing = request.env['education.exam.revaluation'].sudo().search([
            ('student_id', '=', partner.id),
            ('exam_id', '=', exam_id),
            ('course_id', '=', course_id),
            ('state', '!=', 'cancel')
        ], limit=1)
        if existing:
            return request.render(
                'education_exam.portal_revaluation_form',
                {
                    'error_message': "Revaluation already applied for this subject and exam."
                }
            )
        request.env['education.exam.revaluation'].sudo().create({
            'student_id': partner.id,
            'exam_id': exam_id,
            'course_id': course_id,
            'program_id': exam.program_id.id,
            'class_id': exam.class_id.id,
            'session_id': exam.session_id.id,
            'state': 'draft',
        })
        return request.render('education_exam.application_success')



