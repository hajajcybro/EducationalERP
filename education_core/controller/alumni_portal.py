# -*- coding: utf-8 -*-
from odoo import http, _
from odoo.http import request
from odoo.exceptions import ValidationError
from .portal_utils import get_alumni_partner, get_portal_redirect


class AlumniPortalController(http.Controller):

    def _get_alumni_or_redirect(self):
        """
        Returns alumni partner if valid.
        If not alumni, redirects to their correct portal.
        """
        partner = get_alumni_partner()
        if not partner:
            redirect_url = get_portal_redirect(request.env.user.partner_id)
            return None, request.redirect(redirect_url)
        return partner, None

    @http.route(['/my/alumni'], type='http', auth='user', website=True)
    def alumni_dashboard(self, **kwargs):
        """
        Alumni home dashboard.
        Shows: profile summary, unread notification count, job board count.
        """
        partner, redirect = self._get_alumni_or_redirect()
        if redirect:
            return redirect

        # Unread notifications count
        unread_notifications = request.env['edu.notification'].sudo().search([
            ('module', '=', 'alumni'),
            ('status', 'in', ['pending', 'sent']),
            ('recipient_ids', 'in', partner.id),
            ('read_by_partner_ids', 'not in', partner.id),
        ])

        # Active job postings count
        job_count = request.env['alumni.job.post'].sudo().search_count([
            ('state', '=', 'published'),
        ])

        return request.render('education_alumni.portal_alumni_dashboard', {
            'alumni': partner,
            'unread_count': len(unread_notifications),
            'job_count': job_count,
        })

    @http.route(['/my/alumni/profile'], type='http', auth='user', website=True)
    def alumni_profile(self, **kwargs):
        """
        Alumni profile page.
        Shows: name, photo, program, batch, alumni_reference, alumni_status,
               graduation_year, contact details.
        """
        partner, redirect = self._get_alumni_or_redirect()
        if redirect:
            return redirect

        return request.render('education_alumni.portal_alumni_profile', {
            'alumni': partner,
        })

    @http.route(['/my/alumni/notifications'], type='http', auth='user', website=True)
    def alumni_notifications(self, **kwargs):
        """
        Alumni notification dashboard.
        Shows all announcements and alerts sent to this alumni by admin.
        Marks fetched notifications as read.
        """
        partner, redirect = self._get_alumni_or_redirect()
        if redirect:
            return redirect

        notifications = request.env['edu.notification'].sudo().search([
            ('module', '=', 'alumni'),
            ('status', 'in', ['pending', 'sent']),
            ('recipient_ids', 'in', partner.id),
        ], order='id desc')

        # Mark all as read
        for notif in notifications:
            if partner.id not in notif.read_by_partner_ids.ids:
                notif.sudo().write({
                    'read_by_partner_ids': [(4, partner.id)]
                })

        return request.render('education_alumni.portal_alumni_notifications', {
            'alumni': partner,
            'notifications': notifications,
        })

    @http.route(['/my/alumni/jobs'], type='http', auth='user', website=True)
    def alumni_jobs(self, **kwargs):
        """
        Job board — lists all published job vacancies posted by alumni.
        Accessible to both alumni and students (read-only for students).
        """
        partner, redirect = self._get_alumni_or_redirect()
        if redirect:
            return redirect

        jobs = request.env['alumni.job.post'].sudo().search([
            ('state', '=', 'published'),
        ], order='id desc')

        return request.render('education_alumni.portal_alumni_jobs', {
            'alumni': partner,
            'jobs': jobs,
        })
