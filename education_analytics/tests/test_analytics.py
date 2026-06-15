# -*- coding: utf-8 -*-
"""
education_analytics — Unit Tests
==================================
Verifies that the four SQL view-backed models are searchable and that the
dashboard AbstractModel returns the expected KPI dict structure.

No setUpClass is needed — the SQL views are created by each model's init()
method at module install time, so they already exist when these tests run.
"""
from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestAnalytics(TransactionCase):
    """Unit tests for edu.analytics.* view models and dashboard provider."""

    # ── SQL view existence tests ───────────────────────────────────────────

    def test_enrollment_summary_view_exists(self):
        """edu.analytics.enrollment.summary SQL view should be searchable without error."""
        results = self.env["edu.analytics.enrollment.summary"].search([])
        # The search itself must not raise; result can be empty in a fresh DB
        self.assertIsNotNone(results)

    def test_fee_collection_view_exists(self):
        """edu.analytics.fee.collection SQL view should be searchable without error."""
        results = self.env["edu.analytics.fee.collection"].search([])
        self.assertIsNotNone(results)

    def test_attendance_rate_view_exists(self):
        """edu.analytics.attendance.rate SQL view should be searchable without error."""
        results = self.env["edu.analytics.attendance.rate"].search([])
        self.assertIsNotNone(results)

    def test_exam_pass_rate_view_exists(self):
        """edu.analytics.exam.pass.rate SQL view should be searchable without error."""
        results = self.env["edu.analytics.exam.pass.rate"].search([])
        self.assertIsNotNone(results)

    # ── Dashboard KPI method test ──────────────────────────────────────────

    def test_admin_kpis_returns_dict(self):
        """get_admin_kpis() should return a dict with the expected keys."""
        kpis = self.env["edu.analytics.dashboard"].get_admin_kpis()

        self.assertIsInstance(kpis, dict, "get_admin_kpis() must return a dict")
        self.assertIn(
            "total_students", kpis,
            "KPI dict must contain 'total_students'",
        )
        self.assertIn(
            "pending_fees_count", kpis,
            "KPI dict must contain 'pending_fees_count'",
        )
        self.assertIn(
            "attendance_rate", kpis,
            "KPI dict must contain 'attendance_rate'",
        )
        # Value types — integers / floats, never None
        self.assertIsInstance(kpis["total_students"], int)
        self.assertIsInstance(kpis["pending_fees_count"], int)
        self.assertIsInstance(kpis["attendance_rate"], float)
