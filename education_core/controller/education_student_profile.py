from odoo import http
from odoo.http import request
from .portal_utils import get_student_partner


class StudentPortalController(http.Controller):
    @http.route(['/my/profile'], type='http', auth='user', website=True)
    def portal_student_profile(self, **kwargs):
        """
                Display the Student Profile page in the portal.
                - Retrieves the logged-in student partner record.
                - Ensures the user has position_role = 'student'.
                - Fetches approved education documents linked to the student.
                - Renders the student profile template with student
                  and document details.
        """
        partner = get_student_partner()
        # unread_notifications = request.env['edu.notification'].sudo().search([
        #     ('module', '=', 'document'),
        #     ('status', 'in', ['pending', 'sent']),
        #     ('recipient_ids', 'in', partner.id),
        #     ('read_by_partner_ids', 'not in', partner.id)
        # ])
        # alert_messages = [n.message for n in unread_notifications if n.message]
        # # Mark all as read
        # for notif in unread_notifications:
        #     notif.sudo().write({'read_by_partner_ids': [(4, partner.id)]})

        if not partner.position_role == 'student':
            return request.redirect('/my')
        return request.render('education_core.portal_student_profile', {
            'student': partner,
            # 'alert_messages': alert_messages,

        })