# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
from odoo.addons.education_core.controller.alumni_portal import AlumniPortalController

class AlumniPortalNotificationController(AlumniPortalController):

    @http.route()
    def alumni_dashboard(self, **kwargs):
        response = super(AlumniPortalNotificationController, self).alumni_dashboard(**kwargs)
        if hasattr(response, 'qcontext'):
            partner = response.qcontext.get('alumni')
            if partner:
                unread = request.env['edu.notification'].sudo().search_count([
                    ('module', '=', 'alumni'),
                    ('status', 'in', ['pending', 'sent']),
                    ('recipient_ids', 'in', partner.id),
                    ('read_by_partner_ids', 'not in', partner.id),
                ])
                response.qcontext['unread_count'] = unread
        return response

    # Add the completely new route for the Notification List
    @http.route(['/my/alumni/notifications'], type='http', auth='user', website=True)
    def alumni_notifications(self, **kwargs):
        partner, redirect = self._get_alumni_or_redirect()
        if redirect: return redirect
        notifications = request.env['edu.notification'].sudo().search([
            ('module', '=', 'alumni'),
            ('status', 'in', ['pending', 'sent']),
            ('recipient_ids', 'in', partner.id),
        ])
        for notif in notifications:
            if partner.id not in notif.read_by_partner_ids.ids:
                notif.sudo().write({'read_by_partner_ids': [(4, partner.id)]})
        return request.render('education_notification.portal_alumni_notifications_list', {
            'alumni': partner,
            'notifications': notifications,
        })