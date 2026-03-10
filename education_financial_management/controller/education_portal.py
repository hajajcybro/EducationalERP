from odoo.addons.portal.controllers.portal import CustomerPortal
from odoo.http import request
from .portal_utils import get_student_partner

class CustomCustomerPortal(CustomerPortal):

    def _prepare_home_portal_values(self, counters):
        # Get default values first
        values = super(CustomCustomerPortal, self)._prepare_home_portal_values(counters)
        partner = get_student_partner()
        if partner:
            unread_notifications = request.env['edu.notification'].sudo().search([
                ('module', '=', 'financial'),
                ('status', 'in', ['pending', 'sent']),
                ('recipient_ids', 'in', partner.id),
                ('read_by_partner_ids', 'not in', partner.id)
            ])
            alert_messages = [n.message for n in unread_notifications if n.message]
            for notif in unread_notifications:
                notif.sudo().write({'read_by_partner_ids': [(4, partner.id)]})
            values['financial_alert_messages'] = alert_messages
        return values