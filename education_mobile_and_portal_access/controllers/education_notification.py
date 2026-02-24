from odoo import http
from odoo.http import request
from .portal_utils import get_student_partner

class NotificationPortal(http.Controller):

    @http.route(['/my/notifications'], type='http', auth='user', website=True)
    def portal_my_notifications(self, **kwargs):
        # partner = request.env.user.partner_id
        partner = get_student_partner()
        # Fetch notifications
        notifications = request.env['education.notification'].sudo().search([
            ('recipient_id', '=', partner.id)
        ])
        # Mark as read
        unread = notifications.filtered(lambda n: not n.is_read)
        if unread:
            unread.sudo().write({'is_read': True})

        return request.render('education_mobile_and_portal_access.portal_notifications_list', {
            'notifications': notifications,
            'page_name': 'notifications'  # Helps with portal breadcrumbs
        })