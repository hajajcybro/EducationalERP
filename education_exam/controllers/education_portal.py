from odoo.addons.portal.controllers.portal import CustomerPortal
from odoo.http import request
from .portal_utils import get_student_partner


class CustomPortalDashboard(CustomerPortal):

    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        partner = get_student_partner()
        if not partner:
            return values
        unread_exam = request.env['edu.notification'].sudo().search([
            ('module', '=', 'exam'),
            ('status', 'in', ['pending', 'sent']),
            ('recipient_ids', 'in', partner.id),
            ('read_by_partner_ids', 'not in', partner.id)
        ])
        values['unread_exam'] = len(unread_exam)
        values['position_role'] = partner.position_role
        return values
