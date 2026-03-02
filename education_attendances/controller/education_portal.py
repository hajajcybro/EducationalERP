from odoo.addons.portal.controllers.portal import CustomerPortal
from odoo.http import request

class CustomPortalDashboard(CustomerPortal):

    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        partner = request.env.user.partner_id
        unread_notifications = request.env['edu.notification'].sudo().search([
            ('module', '=', 'attendance'),
            ('status', 'in', ['pending', 'sent']),
            ('recipient_ids', 'in', partner.id),
            ('read_by_partner_ids', 'not in', partner.id)
        ])
        values['unread_attendance'] = len(unread_notifications)
        return values