from odoo import http
from odoo.http import request

class StudentLeavePortal(http.Controller):

    @http.route(['/my/attendance'], type='http', auth='user', website=True)
    def portal_leave_home(self, **kwargs):
        return request.render(
            'education_mobile_and_portal_access.portal_leave_home'
        )

    @http.route(['/my/my-attendance'], type='http', auth='user', website=True)
    def portal_attendance(self, **kwargs):
        partner = request.env.user.partner_id
        if not partner.is_student:
            return request.redirect('/my')

        return request.render(
            'education_mobile_and_portal_access.portal_attendance_calendar'
        )

    @http.route('/my/my-attendance/events',type='json',auth='user',website=True)
    def portal_attendance_events(self):
        partner = request.env.user.partner_id
        if not partner.is_student:
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
        return request.render(
            'education_mobile_and_portal_access.portal_leave_apply_form'
        )

    @http.route(['/my/leave/submit'], type='http', auth='user', website=True, csrf=True)
    def portal_leave_submit(self, **post):
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

    @http.route(['/my/leave/history'], type='http', auth='user', website=True)
    def portal_leave_history(self, **kwargs):
        partner = request.env.user.partner_id

        leaves = request.env['education.leave.request'].sudo().search([
            ('student_id', '=', partner.id)
        ])

        return request.render(
            'education_mobile_and_portal_access.portal_leave_history',
            {'leaves': leaves}
        )



