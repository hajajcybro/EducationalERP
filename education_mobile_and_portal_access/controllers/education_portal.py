from odoo.addons.portal.controllers.portal import CustomerPortal
from odoo.http import request


class CustomPortalDashboard(CustomerPortal):

    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        partner = request.env.user.partner_id

        # ---------------------------------------------------
        # Single query for ALL modules — grouped by module
        # ---------------------------------------------------
        all_unread = request.env['edu.notification'].sudo().read_group(
            domain=[
                ('status', 'in', ['pending', 'sent']),
                ('recipient_ids', 'in', partner.id),
                ('read_by_partner_ids', 'not in', partner.id),
                ('module', 'in', [
                    'attendance', 'exam', 'library',
                    'scholarship', 'transport', 'profile'
                ]),
            ],
            fields=['module'],
            groupby=['module'],
        )

        # Build a lookup dict: { 'attendance': 3, 'exam': 1, ... }
        counts = {row['module']: row['module_count'] for row in all_unread}

        values['unread_attendance'] = counts.get('attendance', 0)
        values['unread_exam'] = counts.get('exam', 0)
        values['unread_library'] = counts.get('library', 0)
        values['unread_scholarship'] = counts.get('scholarship', 0)
        values['unread_transport'] = counts.get('transport', 0)
        values['unread_profile'] = counts.get('profile', 0)

        return values

    def _get_and_mark_read(self, partner, module):
        """
        Fetch all unread notification messages for a given module + partner,
        mark them as read in one batch write, return list of message strings.
        """
        notifications = request.env['edu.notification'].sudo().search([
            ('module', '=', module),
            ('status', 'in', ['pending', 'sent']),
            ('recipient_ids', 'in', partner.id),
            ('read_by_partner_ids', 'not in', partner.id)
        ])
        messages = [n.message for n in notifications if n.message]
        if notifications:
            notifications.sudo().write({'read_by_partner_ids': [(4, partner.id)]})
        return messages

    # # def _prepare_home_portal_values(self, counters):
    # #     # Get default values first
    # #     values = super()._prepare_home_portal_values(counters)
    # #     partner = request.env.user.partner_id
    # #
    # #     # Count unread notifications specifically for the 'Attendance' module
    # #     unread_notifications = request.env['edu.notification'].sudo().search([
    # #         ('module', '=', 'attendance'),
    # #         ('status', 'in', ['pending', 'sent']),
    # #         ('recipient_ids', 'in', partner.id),
    # #         ('read_by_partner_ids', 'not in', partner.id)
    # #     ])
    # #     values['unread_attendance'] = len(unread_notifications)
    # #
    # #     # Count unread notifications specifically for the 'Exam' module
    # #     unread_exam = request.env['edu.notification'].sudo().search([
    # #         ('module', '=', 'exam'),
    # #         ('status', 'in', ['pending', 'sent']),
    # #         ('recipient_ids', 'in', partner.id),
    # #         ('read_by_partner_ids', 'not in', partner.id)
    # #     ])
    # #     values['unread_exam'] = len(unread_exam)
    # #
    # #     unread_library = request.env['edu.notification'].sudo().search([
    # #         ('module', '=', 'library'),
    # #         ('status', 'in', ['pending', 'sent']),
    # #         ('recipient_ids', 'in', partner.id),
    # #         ('read_by_partner_ids', 'not in', partner.id)
    # #     ])
    # #     values['unread_library'] = len(unread_library)
    # #
    # #     unread_scholarship = request.env['edu.notification'].sudo().search([
    # #         ('module', '=', 'scholarship'),
    # #         ('status', 'in', ['pending', 'sent']),
    # #         ('recipient_ids', 'in', partner.id),
    # #         ('read_by_partner_ids', 'not in', partner.id)
    # #     ])
    #     values['unread_scholarship'] = len(unread_scholarship)
    #
    #     unread_transport = request.env['edu.notification'].sudo().search([
    #         ('module', '=', 'transport'),
    #         ('status', 'in', ['pending', 'sent']),
    #         ('recipient_ids', 'in', partner.id),
    #         ('read_by_partner_ids', 'not in', partner.id)
    #     ])
    #     values['unread_transport'] = len(unread_transport)
    #
    #     unread_profile = request.env['edu.notification'].sudo().search([
    #         ('module', '=', 'document'),
    #         ('status', 'in', ['pending', 'sent']),
    #         ('recipient_ids', 'in', partner.id),
    #         ('read_by_partner_ids', 'not in', partner.id)
    #     ])
    #     values['unread_profile'] = len(unread_profile)
    #
    #     return values
