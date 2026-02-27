from odoo import http
from odoo.http import request
from .portal_utils import get_student_partner


class StudentLeavePortal(http.Controller):

    @http.route(['/my/leave'], type='http', auth='user', website=True)
    def portal_leave_home(self, **kwargs):
        partner = request.env.user.partner_id
        # unread_notifications = request.env['edu.notification'].sudo().search([
        #     ('module', '=', 'attendance'),
        #     ('recipient_ids', 'in', partner.id),
        #     ('read_by_partner_ids', 'not in', partner.id)
        # ])
        # if unread_notifications:
        #     unread_notifications.sudo().write({
        #         'read_by_partner_ids': [(4, partner.id)]
        #     })
        # # alert_messages = [notif.message for notif in unread_notifications if notif.message]
        # values = {
        #     'alert_messages': alert_messages,
        # }
        return request.render(
            'education_attendances.portal_leave_home',
        )

    @http.route(['/my/leave/apply'], type='http', auth='user', website=True)
    def portal_leave_apply_form(self, **kwargs):
        """
          Render the Leave Application form in the student portal.
          - Redirects non-student users to '/my'.
          - Displays the leave application form template.
          """
        partner = request.env.user.partner_id
        if partner.position_role != 'student':
            return request.redirect('/my')
        return request.render(
            'education_attendances.portal_leave_apply_form'
        )

    @http.route(['/my/leave/submit'], type='http', auth='user', website=True, csrf=True)
    def portal_leave_submit(self, **post):
        """
            Handle submission of a Leave Application from the portal.
            - Retrieves the logged-in student's partner record.
            - Creates a new education.leave.request record using submitted form data.
            - Links the leave request to the student.
            - Redirects the user back to '/my' after successful submission.
            """
        partner = request.env.user.partner_id
        request.env['education.leave.request'].sudo().create({
            'student_id': partner.id,
            'leave_format': post.get('leave_format'),
            'session': post.get('session'),
            'start_date': post.get('start_date'),
            'end_date': post.get('end_date'),
            'reason': post.get('reason'),
        })
        return request.redirect('/my/leave/history')

    @http.route(['/my/leave/history'], auth='user', website=True)
    def portal_leave_history(self, **kwargs):
        """
            Display the Leave History page in the student portal.
            - Retrieves the logged-in student's partner record.
            - Fetches all leave requests linked to the student.
            - Renders the leave history template with leave records.
            """
        partner = get_student_partner()
        # partner = request.env.user.partner_id

        # Sudo is used to bypass record rules and fetch records for the portal view
        leaves = request.env['education.leave.request'].sudo().search([
            ('student_id', '=', partner.id),
        ])
        print(leaves.student_id)
        print(partner)
        # print(student)
        return request.render(
            'education_attendances.portal_leave_history',
            {'leaves': leaves}
        )
