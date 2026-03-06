from odoo import http
from odoo.http import request
from odoo import fields, models
from .portal_utils import get_student_partner

class AlumniExamPortal(http.Controller):

    @http.route(['/my/alumni/exam/supply'], type='http', auth='user', website=True)
    def portal_supply_form(self, **kwargs):
        student = get_student_partner()
        if student.position_role != 'alumni':
            return request.redirect('/my/exams')
        failed_lines = request.env['education.exam.result.line'].sudo().search([
            ('result_id.student_id', '=', student.id),
            ('pass_or_fail', '=', False)
        ])
        failed_courses = failed_lines.mapped('course_id')
        available_exams = request.env['education.exam'].sudo().search([
            ('state', '=', 'published'),
            ('exam_type_id.name', 'ilike', 'Supply')
        ])
        return request.render('education_exam.portal_supply_form', {
            'student': student,
            'failed_courses': failed_courses,
            'available_exams': available_exams,
        })

    @http.route(['/my/alumni/exam/supply/submit'], type='http', auth='user', website=True, csrf=True, methods=['POST'])
    def portal_supply_submit(self, **post):
        """ Handle submission of a Supply Application """
        student = get_student_partner()
        exam_id = int(post.get('exam_id'))
        course_id = int(post.get('course_id'))
        exam = request.env['education.exam'].sudo().browse(exam_id)
        existing = request.env['education.exam.supplementary'].sudo().search([
            ('student_id', '=', student.id),
            ('exam_id', '=', exam_id),
            ('course_id', '=', course_id),
            # ('state', '!=', 'cancel')
        ], limit=1)
        if existing:
            return request.redirect('/my/alumni/exam/supply?error=already_applied')
        request.env['education.exam.supplementary'].sudo().create({
            'student_id': student.id,
            'exam_id': exam_id,
            'course_id': course_id,
            'program_id': exam.program_id.id,
            'session_id': exam.session_id.id,
        })
        return request.redirect('/my/exams?success=1')

    def _send_exam_published_notifications(self, is_supply=False):
        """Send Announcements to the portal notification dashboard."""
        if is_supply and self.program_id:
            # Broadcast to ALL Alumni of this program
            targets = self.env['res.partner'].search([
                ('position_role', '=', 'alumni'),
                ('program_id', '=', self.program_id.id)
            ])
            # CRITICAL FIX: The Alumni Notification Dashboard only reads module='alumni'
            module_type = 'alumni'
            notif_name = f'New Supplementary Exam Published: {self.name}'
            notif_message = f'A new supplementary exam "{self.name}" has been published. Please check the Exams section in your portal for details or to apply.'
        else:
            targets = self.env['res.partner'].search([
                ('class_id', '=', self.class_id.id),
                ('position_role', '=', 'student')
            ])
            module_type = 'exam'
            notif_name = f'New Exam Published: {self.name}'
            notif_message = f'A new exam "{self.name}" has been published. Please check the Exams section for details.'
        recipient_ids = [(4, target.id) for target in targets]
        if recipient_ids:
            notif = self.env['edu.notification'].sudo().create({
                'name': notif_name,
                'message': notif_message,
                'recipient_ids': recipient_ids,
                'module': module_type,
                'notification_type': 'in_app',  # Matches your dashboard logic
            })
            notif.action_send()