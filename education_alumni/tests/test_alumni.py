# -*- coding: utf-8 -*-
"""
education_alumni — Unit Tests
==============================
Covers:
  - Alumni record creation and related student_name field
  - graduation_date / graduation_year auto-derived from the enrollment
  - Unique enrollment constraint
  - Default ordering (graduation_year desc)
"""
from datetime import date, timedelta
from odoo.tests.common import TransactionCase, tagged
from odoo.exceptions import ValidationError


@tagged("post_install", "-at_install")
class TestAlumni(TransactionCase):
    """Unit tests for the edu.alumni model."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # ── Minimal academic year ──────────────────────────────────────────
        cls.academic_year = cls.env["education.academic.year"].create({
            "name": "Alumni Test Year 2025-2026",
            "code": "ALMTST26",
            "date_start": date(2025, 7, 1),
            "date_end": date(2026, 6, 30),
            "is_current": False,
        })

        # ── Department + Program ───────────────────────────────────────────
        cls.department = cls.env["education.department"].create({
            "name": "Alumni Test Department",
            "code": "ALMDEPT",
        })
        cls.program = cls.env["education.program"].create({
            "name": "Alumni Test Program",
            "code": "ALMPROG",
            "department_id": cls.department.id,
            "degree_type": "bachelor",
            "duration_years": 3,
        })

        # ── Application → approval → enrollment ───────────────────────────
        cls.application = cls.env["education.application"].create({
            "first_name": "Alumni",
            "last_name": "Student",
            "date_of_birth": date.today() - timedelta(days=365 * 22),
            "gender": "female",
            "email": "alumni.student@example.com",
            "phone": "2222222222",
            "program_id": cls.program.id,
            "academic_year_id": cls.academic_year.id,
        })
        cls.application.action_submit()
        cls.application.action_approve()
        cls.enrollment = cls.application.enrollment_id

    # ── Helpers ────────────────────────────────────────────────────────────

    def _make_second_enrollment(self):
        """Create a second independent enrollment for ordering/constraint tests."""
        academic_year2 = self.env["education.academic.year"].create({
            "name": "Alumni Test Year 2026-2027",
            "code": "ALMTST27",
            "date_start": date(2026, 7, 1),
            "date_end": date(2027, 6, 30),
            "is_current": False,
        })
        application2 = self.env["education.application"].create({
            "first_name": "Second",
            "last_name": "Alumnus",
            "date_of_birth": date.today() - timedelta(days=365 * 21),
            "gender": "male",
            "email": "second.alumnus@example.com",
            "phone": "3333333333",
            "program_id": self.program.id,
            "academic_year_id": academic_year2.id,
        })
        application2.action_submit()
        application2.action_approve()
        return application2.enrollment_id

    # ── Tests ──────────────────────────────────────────────────────────────

    def test_alumni_created(self):
        """Creating an alumni record saves it and populates student_name via related field."""
        alumni = self.env["edu.alumni"].create({
            "enrollment_id": self.enrollment.id,
        })
        self.assertTrue(alumni.id, "Alumni record should be saved with a valid id")
        self.assertEqual(
            alumni.student_name, self.enrollment.student_name,
            "student_name related field should match the enrollment student name",
        )

    def test_graduation_auto_derived(self):
        """graduation_date / graduation_year are computed from the enrollment.

        Academic year 2025-07-01 → 2026-06-30 on a 3-year program means the
        student graduates at the end of the final year: 2028-06-30.
        """
        alumni = self.env["edu.alumni"].create({
            "enrollment_id": self.enrollment.id,
        })
        self.assertEqual(alumni.graduation_date, date(2028, 6, 30))
        self.assertEqual(alumni.graduation_year, 2028)

    def test_unique_enrollment(self):
        """Creating a second alumni record with the same enrollment_id raises an exception."""
        self.env["edu.alumni"].create({
            "enrollment_id": self.enrollment.id,
        })
        with self.assertRaises(Exception):
            self.env["edu.alumni"].create({
                "enrollment_id": self.enrollment.id,
            })

    def test_ordering(self):
        """Alumni search should return records ordered by graduation_year descending."""
        enrollment2 = self._make_second_enrollment()

        # self.enrollment → academic year 2025-2026 → graduates 2028
        alumni_older = self.env["edu.alumni"].create({
            "enrollment_id": self.enrollment.id,
        })
        # enrollment2 → academic year 2026-2027 → graduates 2029
        alumni_newer = self.env["edu.alumni"].create({
            "enrollment_id": enrollment2.id,
        })
        self.assertEqual(alumni_older.graduation_year, 2028)
        self.assertEqual(alumni_newer.graduation_year, 2029)

        results = self.env["edu.alumni"].search([
            ("id", "in", [alumni_older.id, alumni_newer.id]),
        ])
        # _order = "graduation_year desc, student_name" — newer year comes first
        self.assertEqual(
            results[0].id, alumni_newer.id,
            "Alumni with the higher graduation_year should appear first in search results",
        )
