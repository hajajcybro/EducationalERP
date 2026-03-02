from odoo import http
from odoo.http import request
from .portal_utils import get_student_partner


class StudentLeavePortal(http.Controller):

    @http.route(['/my/attendance'], type='http', auth='user', website=True)
    def portal_leave_home(self, **kwargs):
        """
            Render the Attendance home page in the website portal.
            This route displays the main attendance entry page
            accessible to authenticated users through the portal.
            """
        partner = request.env.user.partner_id
        unread_notifications = request.env['edu.notification'].sudo().search([
            ('module', '=', 'attendance'),
            ('recipient_ids', 'in', partner.id),
            ('read_by_partner_ids', 'not in', partner.id)
        ])
        if unread_notifications:
            unread_notifications.sudo().write({
                'read_by_partner_ids': [(4, partner.id)]
            })
        alert_messages = [notif.message for notif in unread_notifications if notif.message]
        values = {
            'alert_messages': alert_messages,
        }
        return request.render(
            'education_mobile_and_portal_access.portal_leave_home',values
        )

    @http.route(['/my/my-attendance'], type='http', auth='user', website=True)
    def portal_attendance(self, **kwargs):
        """
           Render the student attendance calendar view in the portal.
           - Fetches the logged-in student's partner record.
           - Verifies that the user has the 'student' position_role.
           - Redirects non-student users to '/my'.
           - Displays the attendance calendar template for students.
           """
        partner = get_student_partner()
        if not partner.position_role =='student':
            return request.redirect('/my')

        return request.render(
            'education_mobile_and_portal_access.portal_attendance_calendar'
        )

    @http.route('/my/my-attendance/events',type='jsonrpc',auth='user',website=True)
    def portal_attendance_events(self):
        """
           Provide attendance event data for the student portal calendar (JSON-RPC).
           - Retrieves the logged-in student's partner record.
           - Fetches validated attendance lines for the student.
           - Formats attendance records into calendar event dictionaries.
           - Applies color coding based on attendance status:
               * present → green
               * absent  → red
               * leave   → yellow
               * late    → blue
           - Returns a list of event objects compatible with calendar views.
           """
        partner = get_student_partner()
        if not partner.position_role == 'student':
            return []
        attendance_lines = request.env['education.attendance.line'].sudo().search([
            ('student_id', '=', partner.id),
            ('attendance_id.state', '=', 'validated')
        ])
        events = []
        for line in attendance_lines:
            status = line.status
            date = line.attendance_id.date
            color_map = {
                'present': '#28a745',
                'absent': '#dc3545',
                'leave': '#ffc107',
                'late': '#17a2b8',
            }
            events.append({
                'title': status.capitalize(),
                'start': str(date),
                'allDay': True,
                'color': color_map.get(status, '#6c757d'),
            })
        return events

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
            'education_mobile_and_portal_access.portal_leave_apply_form'
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
        return request.redirect('/my')

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
            'education_mobile_and_portal_access.portal_leave_history',
            {'leaves': leaves}
        )
