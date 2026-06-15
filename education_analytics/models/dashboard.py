# -*- coding: utf-8 -*-
"""
education_analytics — Dashboard data provider (S7-T10, S7-T11, S7-T12, S7-T13)
================================================================================
AbstractModel with @api.model methods that return KPI dicts consumed by OWL
dashboard components.
"""
from odoo import models, api, fields


class EduAnalyticsDashboard(models.AbstractModel):
    """Dashboard data provider — no table, only RPC-callable @api.model methods."""

    _name = "edu.analytics.dashboard"
    _description = "Education Analytics Dashboard Provider"

    # ── Admin Dashboard (S7-T10) ──────────────────────────────────────────

    @api.model
    def get_admin_kpis(self):
        """
        Return KPIs for the Admin dashboard.

        :return: dict with keys:
            - total_students (int)
            - pending_fees_count (int)
            - attendance_rate (float)
        """
        Enrollment = self.env["education.enrollment"]

        total_students = Enrollment.search_count([("state", "=", "active")])

        pending_fees_count = Enrollment.search_count([
            ("state", "=", "active"),
            ("fee_state", "in", ["overdue", "invoiced", "partial"]),
        ])

        # Average attendance rate across all classes
        self.env.cr.execute("""
            SELECT COALESCE(AVG(attendance_rate), 0)
            FROM edu_analytics_attendance_rate
        """)
        row = self.env.cr.fetchone()
        attendance_rate = round(row[0] if row else 0.0, 2)

        return {
            "total_students": total_students,
            "pending_fees_count": pending_fees_count,
            "attendance_rate": attendance_rate,
        }

    # ── Teacher Dashboard (S7-T11) ────────────────────────────────────────

    @api.model
    def get_teacher_kpis(self, teacher_partner_id):
        """
        Return KPIs for the Teacher dashboard.

        :param teacher_partner_id: res.partner id of the teacher
        :return: dict with keys:
            - class_count (int)
            - attendance_pending (int)  — classes with no attendance today
            - lms_completion_avg (float)
        """
        Class = self.env["education.class"]
        today = fields.Date.today()

        # Classes where this partner is the class teacher
        teacher_classes = Class.search([
            ("class_teacher_id", "=", teacher_partner_id),
            ("active", "=", True),
        ])
        class_count = len(teacher_classes)

        # Attendance pending: classes that have no attendance record for today
        attendance_pending = 0
        Attendance = self.env["education.attendance"]
        for cls in teacher_classes:
            count = Attendance.search_count([
                ("class_id", "=", cls.id),
                ("date", "=", today),
            ])
            if count == 0:
                attendance_pending += 1

        # LMS completion average — attempt via edu.lms.enrollment if available
        lms_completion_avg = 0.0
        if "edu.lms.enrollment" in self.env:
            self.env.cr.execute("""
                SELECT COALESCE(AVG(completion_percent), 0)
                FROM edu_lms_enrollment
                WHERE state != 'cancelled'
            """)
            row = self.env.cr.fetchone()
            lms_completion_avg = round(row[0] if row else 0.0, 2)

        return {
            "class_count": class_count,
            "attendance_pending": attendance_pending,
            "lms_completion_avg": lms_completion_avg,
        }

    # ── Accountant Dashboard (S7-T13) ─────────────────────────────────────

    @api.model
    def get_accountant_kpis(self):
        """
        Return KPIs for the Accountant dashboard.

        :return: dict with keys:
            - total_collected (float)
            - total_outstanding (float)
            - overdue_count (int)
        """
        self.env.cr.execute("""
            SELECT
                COALESCE(SUM(total_paid), 0)        AS total_collected,
                COALESCE(SUM(total_outstanding), 0) AS total_outstanding,
                COALESCE(SUM(overdue_count), 0)     AS overdue_count
            FROM edu_analytics_fee_collection
        """)
        row = self.env.cr.fetchone()
        if row:
            total_collected = round(row[0], 2)
            total_outstanding = round(row[1], 2)
            overdue_count = int(row[2])
        else:
            total_collected = 0.0
            total_outstanding = 0.0
            overdue_count = 0

        return {
            "total_collected": total_collected,
            "total_outstanding": total_outstanding,
            "overdue_count": overdue_count,
        }

    # ── Student Dashboard (S7-T12) ────────────────────────────────────────

    @api.model
    def get_student_kpis(self, enrollment_id):
        """
        Return KPIs for the Student dashboard.

        :param enrollment_id: education.enrollment id
        :return: dict with keys:
            - grades_avg (float)
            - attendance_pct (float)
            - fee_status (str)
            - course_progress (float)  — LMS completion %
        """
        enrollment = self.env["education.enrollment"].browse(enrollment_id)
        if not enrollment.exists():
            return {
                "grades_avg": 0.0,
                "attendance_pct": 0.0,
                "fee_status": "not_invoiced",
                "course_progress": 0.0,
            }

        # Grades average — percentage across all published results
        self.env.cr.execute("""
            SELECT COALESCE(AVG(percentage), 0)
            FROM edu_exam_result
            WHERE enrollment_id = %s
              AND state = 'published'
              AND absent = FALSE
        """, (enrollment_id,))
        row = self.env.cr.fetchone()
        grades_avg = round(row[0] if row else 0.0, 2)

        # Attendance percentage
        self.env.cr.execute("""
            SELECT
                COUNT(*) AS total,
                COUNT(*) FILTER (WHERE state IN ('present', 'late')) AS present
            FROM education_attendance
            WHERE enrollment_id = %s
        """, (enrollment_id,))
        row = self.env.cr.fetchone()
        if row and row[0]:
            attendance_pct = round(row[1] * 100.0 / row[0], 2)
        else:
            attendance_pct = 0.0

        fee_status = enrollment.fee_state or "not_invoiced"

        # LMS course progress
        course_progress = 0.0
        if "edu.lms.enrollment" in self.env:
            self.env.cr.execute("""
                SELECT COALESCE(AVG(completion_percent), 0)
                FROM edu_lms_enrollment
                WHERE student_enrollment_id = %s
                  AND state != 'cancelled'
            """, (enrollment_id,))
            row = self.env.cr.fetchone()
            course_progress = round(row[0] if row else 0.0, 2)

        return {
            "grades_avg": grades_avg,
            "attendance_pct": attendance_pct,
            "fee_status": fee_status,
            "course_progress": course_progress,
        }

    # ── Parent Dashboard (S7-T12) ─────────────────────────────────────────

    @api.model
    def get_parent_kpis(self, guardian_partner_id):
        """
        Return a summary list for the Parent/Guardian dashboard.

        :param guardian_partner_id: res.partner id of the guardian
        :return: list of dicts (one per child enrollment), each containing
            the same keys as get_student_kpis plus student_name
        """
        enrollments = self.env["education.enrollment"].search([
            ("guardian_partner_id", "=", guardian_partner_id),
            ("state", "=", "active"),
        ])
        result = []
        for enr in enrollments:
            kpis = self.get_student_kpis(enr.id)
            kpis["student_name"] = enr.student_name
            kpis["enrollment_id"] = enr.id
            result.append(kpis)
        return result
