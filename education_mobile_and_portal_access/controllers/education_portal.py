from odoo.addons.portal.controllers.portal import CustomerPortal
from odoo.http import request


class CustomPortalDashboard(CustomerPortal):

    def _prepare_home_portal_values(self, counters):
        # Get default values first
        values = super()._prepare_home_portal_values(counters)
        partner = request.env.user.partner_id

        # Count unread notifications specifically for the 'Attendance' module
        unread_notifications = request.env['edu.notification'].sudo().search([
            ('module', '=', 'attendance'),
            ('status', 'in', ['pending', 'sent']),
            ('recipient_ids', 'in', partner.id),
            ('read_by_partner_ids', 'not in', partner.id)
        ])
        values['unread_attendance'] = len(unread_notifications)

        # Count unread notifications specifically for the 'Exam' module
        unread_exam = request.env['edu.notification'].sudo().search([
            ('module', '=', 'exam'),
            ('status', 'in', ['pending', 'sent']),
            ('recipient_ids', 'in', partner.id),
            ('read_by_partner_ids', 'not in', partner.id)
        ])
        values['unread_exam'] = len(unread_exam)

        unread_library = request.env['edu.notification'].sudo().search([
            ('module', '=', 'library'),
            ('status', 'in', ['pending', 'sent']),
            ('recipient_ids', 'in', partner.id),
            ('read_by_partner_ids', 'not in', partner.id)
        ])
        values['unread_library'] = len(unread_library)

        unread_scholarship = request.env['edu.notification'].sudo().search([
            ('module', '=', 'scholarship'),
            ('status', 'in', ['pending', 'sent']),
            ('recipient_ids', 'in', partner.id),
            ('read_by_partner_ids', 'not in', partner.id)
        ])
        values['unread_scholarship'] = len(unread_scholarship)

        unread_transport = request.env['edu.notification'].sudo().search([
            ('module', '=', 'transport'),
            ('status', 'in', ['pending', 'sent']),
            ('recipient_ids', 'in', partner.id),
            ('read_by_partner_ids', 'not in', partner.id)
        ])
        values['unread_transport'] = len(unread_transport)

        unread_profile = request.env['edu.notification'].sudo().search([
            ('module', '=', 'document'),
            ('status', 'in', ['pending', 'sent']),
            ('recipient_ids', 'in', partner.id),
            ('read_by_partner_ids', 'not in', partner.id)
        ])
        values['unread_profile'] = len(unread_profile)

        unread_hostel = request.env['edu.notification'].sudo().search([
            ('module', '=', 'hostel'),
            ('status', 'in', ['pending', 'sent']),
            ('recipient_ids', 'in', partner.id),
            ('read_by_partner_ids', 'not in', partner.id)
        ])
        values['unread_hostel'] = len(unread_hostel)

        return values
