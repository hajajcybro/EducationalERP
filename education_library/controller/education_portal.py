from odoo.addons.portal.controllers.portal import CustomerPortal
from odoo.http import request
from .portal_utils import get_student_partner


class CustomPortalDashboard(CustomerPortal):

    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        partner = get_student_partner()
        if not partner:
            return values
        unread_library = request.env['edu.notification'].sudo().search([
            ('module', '=', 'library'),
            ('status', 'in', ['pending', 'sent']),
            ('recipient_ids', 'in', partner.id),
            ('read_by_partner_ids', 'not in', partner.id)
        ])
        values['unread_library'] = len(unread_library)
        return values
