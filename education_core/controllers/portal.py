# -*- coding: utf-8 -*-
"""
education_core — Portal Controller (S2-T12)
============================================
Student self-service portal: own profile, enrolled courses, document checklist.
URL scheme:  /student/             — dashboard
             /student/enrollment   — enrollment detail
             /student/documents    — document checklist
"""
from odoo import http, _
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager
from odoo.exceptions import AccessError, MissingError


class EducationPortal(CustomerPortal):
    """Extend CustomerPortal with student-specific pages."""

    def _prepare_home_portal_values(self, counters):
        """Add enrollment count to portal home page."""
        values = super()._prepare_home_portal_values(counters)
        if "enrollment_count" in counters:
            partner = request.env.user.partner_id
            values["enrollment_count"] = request.env["education.enrollment"].search_count([
                ("student_partner_id", "=", partner.id),
                ("state", "=", "active"),
            ])
        return values

    # ── Student Dashboard ─────────────────────────────────────────────────

    @http.route(["/student", "/student/page/<int:page>"], type="http",
                auth="user", website=True)
    def student_dashboard(self, page=1, **kw):
        """Student portal dashboard — enrollment + document summary."""
        partner = request.env.user.partner_id
        enrollments = request.env["education.enrollment"].search([
            ("student_partner_id", "=", partner.id),
        ])
        return request.render(
            "education_core.portal_student_dashboard",
            {
                "enrollments": enrollments,
                "page_name": "student_dashboard",
            },
        )

    # ── Enrollment Detail ─────────────────────────────────────────────────

    @http.route(["/student/enrollment/<int:enrollment_id>"], type="http",
                auth="user", website=True)
    def student_enrollment_detail(self, enrollment_id, **kw):
        """Show a single enrollment with document checklist."""
        partner = request.env.user.partner_id
        enrollment = request.env["education.enrollment"].browse(enrollment_id)
        # Access control: only the enrolled student can view
        if not enrollment.exists() or enrollment.student_partner_id != partner:
            return request.redirect("/student")
        return request.render(
            "education_core.portal_student_enrollment",
            {
                "enrollment": enrollment,
                "documents": enrollment.document_ids,
                "page_name": "student_enrollment",
            },
        )
