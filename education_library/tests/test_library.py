# -*- coding: utf-8 -*-
"""
education_library — Unit Tests
================================
Covers:
  - Member sequence assignment
  - Book available-copies computation
  - Loan issue / return workflow
  - Fine calculation on overdue loans
  - Borrowing-limit enforcement via issue wizard
  - Duplicate-member SQL constraint
"""
from datetime import date, timedelta

from odoo.tests import TransactionCase, tagged
from odoo.exceptions import ValidationError, UserError
from odoo import fields


@tagged("post_install", "-at_install")
class TestLibrary(TransactionCase):
    """Unit tests for the education_library module."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # ── Book category ─────────────────────────────────────────────────
        cls.category = cls.env["edu.library.book.category"].create({
            "name": "Test Category",
            "daily_fine_rate": 2.0,
        })

        # ── Book ──────────────────────────────────────────────────────────
        cls.book = cls.env["edu.library.book"].create({
            "title": "Test Book",
            "author": "Test Author",
            "category_id": cls.category.id,
            "total_copies": 3,
        })

        # ── Supporting academic records ───────────────────────────────────
        cls.academic_year = cls.env["education.academic.year"].create({
            "name": "Library Test Year",
            "code": "LIBYR26",
            "date_start": date(2025, 7, 1),
            "date_end": date(2026, 6, 30),
            "is_current": False,
        })
        cls.department = cls.env["education.department"].create({
            "name": "Library Test Dept",
            "code": "LIBDEPT",
        })
        cls.program = cls.env["education.program"].create({
            "name": "Library Test Program",
            "code": "LIBPROG",
            "department_id": cls.department.id,
            "degree_type": "bachelor",
            "duration_years": 3,
        })

        # ── Two applications → approved → enrollments ─────────────────────
        app1 = cls.env["education.application"].create({
            "first_name": "Alice",
            "last_name": "LIBStudent",
            "date_of_birth": date.today() - timedelta(days=365 * 20),
            "gender": "female",
            "email": "alice.lib@example.com",
            "phone": "1111111111",
            "program_id": cls.program.id,
            "academic_year_id": cls.academic_year.id,
        })
        app1.action_submit()
        app1.action_approve()
        cls.enrollment1 = app1.enrollment_id

        app2 = cls.env["education.application"].create({
            "first_name": "Bob",
            "last_name": "LIBStudent",
            "date_of_birth": date.today() - timedelta(days=365 * 21),
            "gender": "male",
            "email": "bob.lib@example.com",
            "phone": "2222222222",
            "program_id": cls.program.id,
            "academic_year_id": cls.academic_year.id,
        })
        app2.action_submit()
        app2.action_approve()
        cls.enrollment2 = app2.enrollment_id

        # ── Library members ───────────────────────────────────────────────
        cls.member1 = cls.env["edu.library.member"].create({
            "enrollment_id": cls.enrollment1.id,
            "borrowing_limit": 3,
        })
        cls.member2 = cls.env["edu.library.member"].create({
            "enrollment_id": cls.enrollment2.id,
            "borrowing_limit": 1,
        })

    # ── Sequence ──────────────────────────────────────────────────────────

    def test_member_sequence(self):
        """Member no. should be auto-assigned and start with 'LIB/'."""
        self.assertNotEqual(self.member1.member_no, "New")
        self.assertTrue(
            self.member1.member_no.startswith("LIB/"),
            f"Expected 'LIB/' prefix, got: {self.member1.member_no}",
        )

    # ── Available copies ──────────────────────────────────────────────────

    def test_book_available_copies(self):
        """available_copies should equal total_copies when there are no active loans."""
        self.book._compute_available_copies()
        self.assertEqual(self.book.available_copies, self.book.total_copies)

    # ── Loan issue ────────────────────────────────────────────────────────

    def test_issue_loan(self):
        """Creating an 'issued' loan should decrease available_copies by 1."""
        before = self.book.available_copies
        loan = self.env["edu.library.loan"].create({
            "book_id": self.book.id,
            "member_id": self.member1.id,
            "issue_date": fields.Date.today(),
            "due_date": fields.Date.today() + timedelta(days=14),
            "state": "issued",
        })
        self.book._compute_available_copies()
        self.assertEqual(self.book.available_copies, before - 1)
        # Clean up
        loan.write({"state": "returned", "return_date": fields.Date.today()})

    # ── Loan return ───────────────────────────────────────────────────────

    def test_return_loan(self):
        """action_return() should set state=returned, return_date, and fine=0 for on-time loans."""
        loan = self.env["edu.library.loan"].create({
            "book_id": self.book.id,
            "member_id": self.member1.id,
            "issue_date": fields.Date.today(),
            "due_date": fields.Date.today() + timedelta(days=14),
            "state": "issued",
        })
        loan.action_return()
        self.assertEqual(loan.state, "returned")
        self.assertTrue(loan.return_date)
        self.assertEqual(loan.fine_amount, 0.0)

    # ── Fine calculation ──────────────────────────────────────────────────

    def test_fine_calculation(self):
        """Returning a loan 1 day overdue should produce fine = daily_fine_rate * 1."""
        yesterday = fields.Date.today() - timedelta(days=1)
        loan = self.env["edu.library.loan"].create({
            "book_id": self.book.id,
            "member_id": self.member1.id,
            "issue_date": yesterday - timedelta(days=7),
            "due_date": yesterday,
            "state": "issued",
        })
        loan.action_return()
        self.assertEqual(loan.state, "returned")
        expected_fine = self.category.daily_fine_rate * 1
        self.assertAlmostEqual(loan.fine_amount, expected_fine, places=2)

    # ── Borrowing limit ───────────────────────────────────────────────────

    def test_borrowing_limit(self):
        """Issue wizard should raise UserError when member already has loans >= borrowing_limit."""
        # member2 has borrowing_limit=1; create one active loan to hit the limit
        loan = self.env["edu.library.loan"].create({
            "book_id": self.book.id,
            "member_id": self.member2.id,
            "issue_date": fields.Date.today(),
            "due_date": fields.Date.today() + timedelta(days=14),
            "state": "issued",
        })
        self.member2._compute_active_loans_count()

        # Create a second book so availability is not the blocker
        second_book = self.env["edu.library.book"].create({
            "title": "Second Book",
            "category_id": self.category.id,
            "total_copies": 2,
        })

        wizard = self.env["edu.library.issue.wizard"].create({
            "member_id": self.member2.id,
            "book_id": second_book.id,
            "action": "issue",
            "due_date": fields.Date.today() + timedelta(days=14),
        })
        with self.assertRaises(UserError):
            wizard.action_confirm()

        # Clean up
        loan.write({"state": "returned", "return_date": fields.Date.today()})

    # ── Duplicate member constraint ───────────────────────────────────────

    def test_duplicate_member(self):
        """Creating a second member with the same enrollment_id should raise ValidationError."""
        with self.assertRaises(Exception):
            # Unique SQL constraint raises either IntegrityError (wrapped as
            # UserError/ValidationError by Odoo) or ValidationError.
            self.env["edu.library.member"].create({
                "enrollment_id": self.enrollment1.id,
            })
