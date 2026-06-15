# -*- coding: utf-8 -*-
"""
education_integrations — Unit Tests
=====================================
HTTP routes cannot be exercised directly from TransactionCase, so these tests
validate the underlying data-access logic that the controller methods rely on.

Covered:
  - education.enrollment ORM search used by /api/edu/students
  - edu.notification.centre model is registered and searchable
  - education_integrations.edu_portal_dashboard QWeb template ref exists
"""
from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestEduApi(TransactionCase):
    """Unit tests for integrations data layer."""

    # ── enrollment search ──────────────────────────────────────────────────

    def test_enrollment_search_returns_list(self):
        """Searching active enrollments (domain used by /api/edu/students) must not error."""
        enrollments = self.env["education.enrollment"].search(
            [("state", "=", "active")]
        )
        # Must return a recordset (possibly empty in a test DB)
        self.assertIsNotNone(enrollments)

    # ── notification centre model ──────────────────────────────────────────

    def test_notification_centre_own_domain(self):
        """edu.notification.centre model must be registered and searchable."""
        self.assertIn(
            "edu.notification.centre",
            self.env,
            "edu.notification.centre model should be available in the registry",
        )
        records = self.env["edu.notification.centre"].search([])
        self.assertIsNotNone(records)

    # ── portal template xmlid ──────────────────────────────────────────────

    def test_portal_template_exists(self):
        """education_integrations.edu_portal_dashboard QWeb template must exist."""
        template = self.env.ref(
            "education_integrations.edu_portal_dashboard",
            raise_if_not_found=False,
        )
        self.assertIsNotNone(
            template,
            "XML ref 'education_integrations.edu_portal_dashboard' should exist",
        )
