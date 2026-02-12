from odoo import http
from odoo.http import request

class StudentLeavePortal(http.Controller):

    @http.route(['/my/leave'], type='http', auth='user', website=True)
    def portal_leave_home(self, **kwargs):
        return request.render(
            'education_mobile_and_portal_access.portal_leave_home'
        )

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



