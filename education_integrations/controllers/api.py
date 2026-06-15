# -*- coding: utf-8 -*-
"""
education_integrations — REST API Controller (S7-T08)
=====================================================
4 read-only JSON endpoints for external integrations.
All routes require an authenticated (non-public) user.
"""
from odoo import http
from odoo.http import request
from datetime import date


class EduApiController(http.Controller):
    """REST API endpoints for the Education ERP."""

    # ── Auth helper ──────────────────────────────────────────────────────────

    def _check_auth(self):
        """Return a 401 JSON response if the user is public, else None."""
        if request.env.user._is_public():
            return request.make_json_response(
                {"status": "error", "message": "Authentication required"},
                status=401,
            )
        return None

    # ── GET /api/edu/students ────────────────────────────────────────────────

    @http.route(
        "/api/edu/students",
        type="http",
        auth="user",
        methods=["GET"],
        csrf=False,
    )
    def get_students(self, **kwargs):
        """Return JSON list of active enrollments."""
        err = self._check_auth()
        if err:
            return err

        enrollments = request.env["education.enrollment"].search([
            ("state", "=", "active"),
        ])

        data = []
        for enr in enrollments:
            data.append({
                "id": enr.id,
                "admission_no": enr.enrollment_no or "",
                "student_name": enr.student_name or "",
                "class_name": enr.class_id.name if enr.class_id else "",
                "program_name": enr.program_id.name if enr.program_id else "",
                "academic_year": enr.academic_year_id.name if enr.academic_year_id else "",
                "state": enr.state,
            })

        return request.make_json_response({"status": "ok", "data": data})

    # ── GET /api/edu/enrollment/<id> ─────────────────────────────────────────

    @http.route(
        "/api/edu/enrollment/<int:enrollment_id>",
        type="http",
        auth="user",
        methods=["GET"],
        csrf=False,
    )
    def get_enrollment(self, enrollment_id, **kwargs):
        """Return full detail of a single enrollment."""
        err = self._check_auth()
        if err:
            return err

        enr = request.env["education.enrollment"].browse(enrollment_id)
        if not enr.exists():
            return request.make_json_response(
                {"status": "error", "message": "Enrollment not found"},
                status=404,
            )

        data = {
            "id": enr.id,
            "admission_no": enr.enrollment_no or "",
            "student_name": enr.student_name or "",
            "student_email": enr.student_email or "",
            "date_of_birth": str(enr.date_of_birth) if enr.date_of_birth else "",
            "class_name": enr.class_id.name if enr.class_id else "",
            "program_name": enr.program_id.name if enr.program_id else "",
            "department": enr.department_id.name if enr.department_id else "",
            "academic_year": enr.academic_year_id.name if enr.academic_year_id else "",
            "state": enr.state,
            "enrollment_date": str(enr.enrollment_date) if enr.enrollment_date else "",
            "guardian_name": enr.guardian_name or "",
            "guardian_phone": enr.guardian_phone or "",
            "guardian_email": enr.guardian_email or "",
            "doc_completion_pct": enr.doc_completion_pct,
        }

        # Fee fields (from education_financial_management if installed)
        if hasattr(enr, "fee_state"):
            data["fee_state"] = enr.fee_state or "not_invoiced"
            data["amount_due"] = enr.amount_due or 0.0
            data["amount_paid"] = enr.amount_paid or 0.0
            data["total_fee"] = enr.total_fee or 0.0

        return request.make_json_response({"status": "ok", "data": data})

    # ── GET /api/edu/attendance ──────────────────────────────────────────────

    @http.route(
        "/api/edu/attendance",
        type="http",
        auth="user",
        methods=["GET"],
        csrf=False,
    )
    def get_attendance(self, class_id=None, date=None, **kwargs):
        """Return attendance records for a given class/date.

        Query params:
            class_id (int, optional) — filter by education.class id
            date (str, optional)     — YYYY-MM-DD, defaults to today
        """
        err = self._check_auth()
        if err:
            return err

        # Resolve date
        if date:
            try:
                from datetime import datetime
                filter_date = datetime.strptime(date, "%Y-%m-%d").date()
            except (ValueError, TypeError):
                return request.make_json_response(
                    {"status": "error", "message": "Invalid date format. Use YYYY-MM-DD."},
                    status=400,
                )
        else:
            from datetime import date as _date
            filter_date = _date.today()

        domain = [("date", "=", filter_date)]
        if class_id:
            try:
                domain.append(("class_id", "=", int(class_id)))
            except (ValueError, TypeError):
                return request.make_json_response(
                    {"status": "error", "message": "Invalid class_id."},
                    status=400,
                )

        records = request.env["education.attendance"].search(domain)

        data = []
        for att in records:
            data.append({
                "id": att.id,
                "student_name": att.student_name or "",
                "enrollment_id": att.enrollment_id.id if att.enrollment_id else None,
                "class_id": att.class_id.id if att.class_id else None,
                "class_name": att.class_id.name if att.class_id else "",
                "date": str(att.date) if att.date else "",
                "period_no": att.period_no,
                "subject": att.subject or "",
                "state": att.state,
                "notes": att.notes or "",
            })

        return request.make_json_response({"status": "ok", "data": data})

    # ── GET /api/edu/results ─────────────────────────────────────────────────

    @http.route(
        "/api/edu/results",
        type="http",
        auth="user",
        methods=["GET"],
        csrf=False,
    )
    def get_results(self, exam_id=None, student_id=None, **kwargs):
        """Return exam results.

        Query params:
            exam_id    (int, optional) — filter by edu.exam id
            student_id (int, optional) — filter by education.enrollment id
        """
        err = self._check_auth()
        if err:
            return err

        # Check that edu.exam.result model exists (requires education_exam addon)
        if "edu.exam.result" not in request.env:
            return request.make_json_response(
                {"status": "error", "message": "Exam module not installed."},
                status=503,
            )

        domain = []
        if exam_id:
            try:
                domain.append(("exam_id", "=", int(exam_id)))
            except (ValueError, TypeError):
                return request.make_json_response(
                    {"status": "error", "message": "Invalid exam_id."},
                    status=400,
                )
        if student_id:
            try:
                domain.append(("enrollment_id", "=", int(student_id)))
            except (ValueError, TypeError):
                return request.make_json_response(
                    {"status": "error", "message": "Invalid student_id."},
                    status=400,
                )

        results = request.env["edu.exam.result"].search(domain)

        data = []
        for res in results:
            data.append({
                "id": res.id,
                "exam_id": res.exam_id.id if res.exam_id else None,
                "exam_name": res.exam_id.name if res.exam_id else "",
                "enrollment_id": res.enrollment_id.id if res.enrollment_id else None,
                "student_name": res.student_name or "",
                "subject": res.subject or "",
                "marks_obtained": res.marks_obtained,
                "max_marks": res.max_marks,
                "pass_marks": res.pass_marks,
                "percentage": res.percentage,
                "grade": res.grade or "",
                "pass_fail": res.pass_fail or "",
                "rank": res.rank,
                "absent": res.absent,
                "state": res.state,
            })

        return request.make_json_response({"status": "ok", "data": data})
