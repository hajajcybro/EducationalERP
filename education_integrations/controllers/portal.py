# -*- coding: utf-8 -*-
"""
education_integrations — Portal Controller (S7-T14, S7-T15)
============================================================
Extends education_core's portal with:
  /my/education            — Student dashboard (attendance %, fees, LMS, results)
  /my/education/report-card — Download mark sheet PDF for latest exam
  /my/education/children   — Parent portal: list enrolled children
"""
from odoo import http, _
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager


class EduPortalController(CustomerPortal):
    """Extended portal controller for Education ERP."""

    # ── Portal home count ────────────────────────────────────────────────────

    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        partner = request.env.user.partner_id

        if "education_count" in counters:
            values["education_count"] = request.env["education.enrollment"].search_count([
                ("student_partner_id", "=", partner.id),
                ("state", "=", "active"),
            ])

        if "children_count" in counters:
            values["children_count"] = request.env["education.enrollment"].search_count([
                ("guardian_partner_id", "=", partner.id),
                ("state", "=", "active"),
            ])

        return values

    # ── /my/education — Student Dashboard ───────────────────────────────────

    @http.route("/my/education", type="http", auth="user", website=True)
    def education_dashboard(self, **kwargs):
        """Student self-service dashboard."""
        partner = request.env.user.partner_id

        # Current enrollment (most recent active)
        enrollment = request.env["education.enrollment"].search([
            ("student_partner_id", "=", partner.id),
            ("state", "=", "active"),
        ], limit=1, order="enrollment_date desc")

        values = {
            "page_name": "education_dashboard",
            "enrollment": enrollment,
            "attendance_pct": 0.0,
            "amount_due": 0.0,
            "lms_courses": [],
            "recent_results": [],
        }

        if enrollment:
            # Attendance percentage
            attendance_records = request.env["education.attendance"].search([
                ("enrollment_id", "=", enrollment.id),
            ])
            if attendance_records:
                total = len(attendance_records)
                present = len(attendance_records.filtered(
                    lambda a: a.state in ("present", "late")
                ))
                values["attendance_pct"] = round(present / total * 100, 1) if total else 0.0

            # Fee amount due (financial management addon)
            if hasattr(enrollment, "amount_due"):
                values["amount_due"] = enrollment.amount_due or 0.0
                values["fee_state"] = enrollment.fee_state or "not_invoiced"

            # LMS enrollments
            if "edu.lms.enrollment" in request.env:
                lms_enrollments = request.env["edu.lms.enrollment"].search([
                    ("student_id", "=", enrollment.id),
                    ("state", "=", "enrolled"),
                ])
                values["lms_courses"] = lms_enrollments

            # Recent exam results (last 3)
            if "edu.exam.result" in request.env:
                results = request.env["edu.exam.result"].search([
                    ("enrollment_id", "=", enrollment.id),
                    ("state", "=", "published"),
                ], limit=3, order="id desc")
                values["recent_results"] = results

        return request.render(
            "education_integrations.edu_portal_dashboard",
            values,
        )

    # ── /my/education/report-card — Mark Sheet PDF ───────────────────────────

    @http.route("/my/education/report-card", type="http", auth="user", website=True)
    def education_report_card(self, **kwargs):
        """Redirect to mark sheet PDF for the student's latest published exam."""
        partner = request.env.user.partner_id

        enrollment = request.env["education.enrollment"].search([
            ("student_partner_id", "=", partner.id),
            ("state", "=", "active"),
        ], limit=1, order="enrollment_date desc")

        if not enrollment:
            return request.redirect("/my/education")

        if "edu.exam.result" not in request.env:
            return request.redirect("/my/education")

        # Get the latest published exam for this student
        result = request.env["edu.exam.result"].search([
            ("enrollment_id", "=", enrollment.id),
            ("state", "=", "published"),
        ], limit=1, order="id desc")

        if not result:
            return request.redirect("/my/education")

        # Build a simple HTML report card rendered as a page
        results_all = request.env["edu.exam.result"].search([
            ("enrollment_id", "=", enrollment.id),
            ("exam_id", "=", result.exam_id.id),
            ("state", "=", "published"),
        ])

        values = {
            "page_name": "report_card",
            "enrollment": enrollment,
            "exam": result.exam_id,
            "results": results_all,
        }
        return request.render(
            "education_integrations.edu_portal_report_card",
            values,
        )

    # ── /my/education/children — Parent Portal ───────────────────────────────

    @http.route("/my/education/children", type="http", auth="user", website=True)
    def children_dashboard(self, child_id=None, **kwargs):
        """Parent portal: list enrolled children and optionally show one child's detail."""
        partner = request.env.user.partner_id

        children = request.env["education.enrollment"].search([
            ("guardian_partner_id", "=", partner.id),
        ], order="student_name, enrollment_date desc")

        selected = None
        child_attendance_pct = 0.0
        child_results = []
        child_lms = []

        if child_id:
            try:
                child_id_int = int(child_id)
            except (ValueError, TypeError):
                child_id_int = None

            if child_id_int:
                selected = children.filtered(lambda c: c.id == child_id_int)
                selected = selected[:1] if selected else None

        if selected:
            # Attendance %
            att_recs = request.env["education.attendance"].search([
                ("enrollment_id", "=", selected.id),
            ])
            if att_recs:
                total = len(att_recs)
                present = len(att_recs.filtered(lambda a: a.state in ("present", "late")))
                child_attendance_pct = round(present / total * 100, 1) if total else 0.0

            # Recent results
            if "edu.exam.result" in request.env:
                child_results = request.env["edu.exam.result"].search([
                    ("enrollment_id", "=", selected.id),
                    ("state", "=", "published"),
                ], limit=5, order="id desc")

            # LMS courses
            if "edu.lms.enrollment" in request.env:
                child_lms = request.env["edu.lms.enrollment"].search([
                    ("student_id", "=", selected.id),
                    ("state", "=", "enrolled"),
                ])

        values = {
            "page_name": "children_dashboard",
            "children": children,
            "selected": selected,
            "child_attendance_pct": child_attendance_pct,
            "child_results": child_results,
            "child_lms": child_lms,
        }

        return request.render(
            "education_integrations.edu_portal_children",
            values,
        )
