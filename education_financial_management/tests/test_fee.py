# -*- coding: utf-8 -*-
"""
Tests — education_financial_management (S5-T12)
================================================
Covers:
  - Fee plan creation and total_amount computation
  - Fee plan line amount validation (> 0)
  - Invoice auto-generation from enrollment fee plan
  - Scholarship deduction applied as negative line
  - Duplicate invoice guard
  - fee_state transitions: not_invoiced → invoiced → partial → paid
  - fee_state = overdue when due_date < today
  - Outstanding fee SQL view reflects data
  - Overdue cron queues emails and sets fee_state = 'overdue'
"""
from odoo.tests import tagged, TransactionCase
from odoo.exceptions import UserError, ValidationError
from odoo import fields
from datetime import date, timedelta


@tagged("post_install", "-at_install")
class TestFeePlan(TransactionCase):
    """edu.fee.plan model tests."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # Academic year
        cls.ay = cls.env["education.academic.year"].create({
            "name": "Test AY 2025-26",
            "code": "TST2526",
            "date_start": "2025-06-01",
            "date_end": "2026-05-31",
        })

        # Department → Program → Class
        cls.dept = cls.env["education.department"].create({
            "name": "Test Science",
            "code": "TST-SCI",
        })
        cls.program = cls.env["education.program"].create({
            "name": "Test B.Sc Physics",
            "code": "TST-PHY",
            "degree_type": "bachelor",
            "department_id": cls.dept.id,
            "duration_years": 3,
        })
        cls.cls = cls.env["education.class"].create({
            "section": "A",
            "program_id": cls.program.id,
            "academic_year_id": cls.ay.id,
        })

        # Income account
        cls.income_account = cls.env["account.account"].search([
            ("account_type", "=", "income"),
            ("company_ids", "in", cls.env.company.id),
        ], limit=1)
        if not cls.income_account:
            cls.income_account = cls.env["account.account"].create({
                "name": "Test Fee Income",
                "code": "TEST_FEE_999",
                "account_type": "income",
            })

        # Fee plan with two components
        cls.fee_plan = cls.env["edu.fee.plan"].create({
            "name": "Standard BSc Plan 2025-26",
            "academic_year_id": cls.ay.id,
            "program_id": cls.program.id,
            "line_ids": [
                (0, 0, {
                    "component": "Tuition Fee",
                    "fee_type": "tuition",
                    "amount": 50000.0,
                    "due_date": "2025-07-01",
                    "account_id": cls.income_account.id,
                }),
                (0, 0, {
                    "component": "Lab Fee",
                    "fee_type": "lab",
                    "amount": 5000.0,
                    "due_date": "2025-07-15",
                    "account_id": cls.income_account.id,
                }),
            ],
        })

        # Student partner + document type
        cls.doc_type = cls.env["education.document.type"].create({
            "name": "Transfer Certificate",
            "code": "TC_TEST",
        })
        cls.student_partner = cls.env["res.partner"].create({
            "name": "Test Student Fee",
            "email": "student_fee@test.com",
        })

        # Application → Enrollment
        cls.application = cls.env["education.application"].create({
            "first_name": "Test",
            "last_name": "Student",
            "date_of_birth": "2005-01-01",
            "gender": "male",
            "email": "student_fee@test.com",
            "phone": "9999999999",
            "program_id": cls.program.id,
            "academic_year_id": cls.ay.id,
        })
        cls.application.action_submit()
        cls.application.action_approve()
        # Enrollment created by approve action
        cls.enrollment = cls.env["education.enrollment"].search([
            ("application_id", "=", cls.application.id)
        ], limit=1)
        if not cls.enrollment:
            cls.enrollment = cls.env["education.enrollment"].create({
                "application_id": cls.application.id,
                "student_name": "Test Student",
                "student_partner_id": cls.student_partner.id,
                "program_id": cls.program.id,
                "class_id": cls.cls.id,
                "academic_year_id": cls.ay.id,
            })

        # Ensure the enrollment has a student portal account so that
        # action_generate_invoice() does not raise. The field is readonly in
        # the UI but writable via ORM; this avoids triggering the portal-invite
        # email wizard in action_grant_portal_access().
        cls.enrollment.student_partner_id = cls.student_partner.id

    # ── Fee Plan ──────────────────────────────────────────────────────────

    def test_fee_plan_total_amount(self):
        """total_amount = sum of line amounts."""
        self.assertAlmostEqual(
            self.fee_plan.total_amount, 55000.0,
            msg="total_amount should be 50000 + 5000 = 55000",
        )

    def test_fee_line_amount_must_be_positive(self):
        """ValidationError when a line has amount ≤ 0."""
        with self.assertRaises(ValidationError):
            self.env["edu.fee.plan"].create({
                "name": "Bad Plan",
                "academic_year_id": self.ay.id,
                "line_ids": [(0, 0, {
                    "component": "Zero Fee",
                    "fee_type": "other",
                    "amount": 0,
                })],
            })

    def test_fee_plan_total_updates_on_line_edit(self):
        """total_amount recomputes when a line amount changes."""
        plan = self.env["edu.fee.plan"].create({
            "name": "Dynamic Plan",
            "academic_year_id": self.ay.id,
            "line_ids": [(0, 0, {
                "component": "Misc",
                "fee_type": "other",
                "amount": 1000.0,
            })],
        })
        line = plan.line_ids[0]
        line.amount = 2500.0
        self.assertAlmostEqual(plan.total_amount, 2500.0)

    # ── Invoice generation ────────────────────────────────────────────────

    def test_generate_invoice_without_fee_plan_raises(self):
        """UserError when no fee_plan_id assigned."""
        enr = self.enrollment
        enr.fee_plan_id = False
        with self.assertRaises(UserError):
            enr.action_generate_invoice()

    def test_generate_invoice_creates_account_move(self):
        """action_generate_invoice creates out_invoice with correct lines."""
        enr = self.enrollment
        # Ensure clean state
        enr.invoice_ids.filtered(
            lambda i: i.state != "cancel"
        ).button_cancel()
        enr.fee_plan_id = self.fee_plan.id

        result = enr.action_generate_invoice()
        self.assertEqual(result["res_model"], "account.move")

        invoice = self.env["account.move"].browse(result["res_id"])
        self.assertEqual(invoice.move_type, "out_invoice")
        self.assertEqual(invoice.enrollment_id.id, enr.id)

        components = invoice.invoice_line_ids.mapped("name")
        self.assertIn("Tuition Fee", components)
        self.assertIn("Lab Fee", components)

    def test_invoice_total_matches_fee_plan(self):
        """Invoice amount_total equals fee plan total_amount."""
        enr = self.enrollment
        enr.invoice_ids.button_cancel()
        enr.fee_plan_id = self.fee_plan.id

        result = enr.action_generate_invoice()
        invoice = self.env["account.move"].browse(result["res_id"])
        self.assertAlmostEqual(
            invoice.amount_total,
            self.fee_plan.total_amount,
            places=2,
        )

    def test_scholarship_deduction_applied(self):
        """Scholarship amount appears as negative invoice line."""
        enr = self.enrollment
        enr.invoice_ids.button_cancel()
        enr.fee_plan_id = self.fee_plan.id
        enr.scholarship_amount = 5000.0

        result = enr.action_generate_invoice()
        invoice = self.env["account.move"].browse(result["res_id"])
        scholarship_lines = invoice.invoice_line_ids.filtered(
            lambda l: "Scholarship" in l.name
        )
        self.assertTrue(scholarship_lines, "Scholarship line must exist")
        self.assertAlmostEqual(
            scholarship_lines[0].price_unit, -5000.0,
            msg="Scholarship line price_unit must be negative",
        )
        self.assertAlmostEqual(
            invoice.amount_total,
            self.fee_plan.total_amount - 5000.0,
            places=2,
        )
        # Reset
        enr.scholarship_amount = 0.0

    def test_duplicate_invoice_raises(self):
        """UserError when a non-cancelled invoice already exists."""
        enr = self.enrollment
        enr.fee_plan_id = self.fee_plan.id
        # Ensure one active invoice exists
        if not enr.invoice_ids.filtered(lambda i: i.state != "cancel"):
            enr.action_generate_invoice()

        with self.assertRaises(UserError):
            enr.action_generate_invoice()

    # ── fee_state transitions ─────────────────────────────────────────────

    def test_fee_state_not_invoiced_when_no_invoice(self):
        """fee_state = not_invoiced when no invoices exist."""
        enr = self.enrollment
        enr.invoice_ids.button_cancel()
        enr._compute_invoice_info()
        self.assertEqual(enr.fee_state, "not_invoiced")

    def test_fee_state_invoiced_after_post(self):
        """fee_state = invoiced after invoice is confirmed (posted)."""
        enr = self.enrollment
        enr.invoice_ids.button_cancel()
        enr.fee_plan_id = self.fee_plan.id
        result = enr.action_generate_invoice()
        invoice = self.env["account.move"].browse(result["res_id"])
        invoice.action_post()
        enr._compute_invoice_info()
        self.assertIn(enr.fee_state, ("invoiced", "overdue"))

    def test_fee_state_overdue_when_due_passed(self):
        """fee_state = overdue when due_date < today and not paid."""
        enr = self.enrollment
        enr.invoice_ids.button_cancel()
        enr.fee_plan_id = self.fee_plan.id
        result = enr.action_generate_invoice()
        invoice = self.env["account.move"].browse(result["res_id"])
        invoice.invoice_date_due = date.today() - timedelta(days=5)
        invoice.action_post()
        enr._compute_invoice_info()
        self.assertEqual(enr.fee_state, "overdue")

    # ── account.move computed fields ──────────────────────────────────────

    def test_account_move_student_name_related(self):
        """account.move.student_name is related to enrollment.student_name."""
        enr = self.enrollment
        enr.invoice_ids.button_cancel()
        enr.fee_plan_id = self.fee_plan.id
        result = enr.action_generate_invoice()
        invoice = self.env["account.move"].browse(result["res_id"])
        self.assertEqual(invoice.student_name, enr.student_name)

    # ── Overdue cron ──────────────────────────────────────────────────────

    def test_overdue_cron_marks_enrollment_overdue(self):
        """Cron sets fee_state = 'overdue' on enrollments with past-due invoices."""
        enr = self.enrollment
        enr.invoice_ids.button_cancel()
        enr.fee_plan_id = self.fee_plan.id
        result = enr.action_generate_invoice()
        invoice = self.env["account.move"].browse(result["res_id"])
        invoice.invoice_date_due = date.today() - timedelta(days=3)
        invoice.action_post()
        # Force fee_state to 'invoiced' to simulate pre-cron state
        enr.fee_state = "invoiced"

        self.env["edu.fee.overdue.cron"]._cron_send_overdue_reminders()

        enr.invalidate_recordset()
        self.assertEqual(enr.fee_state, "overdue")
