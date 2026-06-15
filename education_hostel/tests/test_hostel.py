# -*- coding: utf-8 -*-
"""
education_hostel — Unit Tests
================================
Covers:
  - Initial room availability
  - Allocation confirm: state + room occupancy
  - Allocation vacate: state + room freed
  - Duplicate active allocation raises UserError
  - date_to < date_from raises ValidationError
  - Property room_count / occupied_count computed fields
"""
from datetime import date, timedelta

from odoo.tests import TransactionCase, tagged
from odoo.exceptions import ValidationError, UserError
from odoo import fields


@tagged("post_install", "-at_install")
class TestHostel(TransactionCase):
    """Unit tests for the education_hostel module."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # ── Hostel property ───────────────────────────────────────────────
        cls.property = cls.env["edu.hostel.property"].create({
            "name": "Test Hostel Block A",
            "total_capacity": 10,
        })

        # ── Room ──────────────────────────────────────────────────────────
        cls.room = cls.env["edu.hostel.room"].create({
            "property_id": cls.property.id,
            "room_no": "101",
            "room_type": "single",
            "capacity": 1,
            "state": "available",
        })

        # ── Enrollment (via application workflow) ─────────────────────────
        cls.academic_year = cls.env["education.academic.year"].create({
            "name": "Hostel Test Year",
            "code": "HSTYR26",
            "date_start": date(2025, 7, 1),
            "date_end": date(2026, 6, 30),
            "is_current": False,
        })
        cls.department = cls.env["education.department"].create({
            "name": "Hostel Test Dept",
            "code": "HSTDEPT",
        })
        cls.program = cls.env["education.program"].create({
            "name": "Hostel Test Program",
            "code": "HSTPROG",
            "department_id": cls.department.id,
            "degree_type": "bachelor",
            "duration_years": 3,
        })
        app = cls.env["education.application"].create({
            "first_name": "Charlie",
            "last_name": "HostelStudent",
            "date_of_birth": date.today() - timedelta(days=365 * 19),
            "gender": "male",
            "email": "charlie.hostel@example.com",
            "phone": "3333333333",
            "program_id": cls.program.id,
            "academic_year_id": cls.academic_year.id,
        })
        app.action_submit()
        app.action_approve()
        cls.enrollment = app.enrollment_id

    # ── Initial state ─────────────────────────────────────────────────────

    def test_room_initially_available(self):
        """A newly created room should have state='available'."""
        self.assertEqual(self.room.state, "available")

    # ── Confirm allocation ────────────────────────────────────────────────

    def test_confirm_allocation(self):
        """action_confirm() should set allocation state=confirmed and room.state=occupied."""
        alloc = self.env["edu.hostel.allocation"].create({
            "enrollment_id": self.enrollment.id,
            "room_id": self.room.id,
            "date_from": fields.Date.today(),
        })
        alloc.action_confirm()
        self.assertEqual(alloc.state, "confirmed")
        self.assertEqual(self.room.state, "occupied")
        # Clean up for other tests
        alloc.action_vacate()

    # ── Vacate allocation ─────────────────────────────────────────────────

    def test_vacate_allocation(self):
        """action_vacate() should set allocation state=vacated and room.state=available."""
        alloc = self.env["edu.hostel.allocation"].create({
            "enrollment_id": self.enrollment.id,
            "room_id": self.room.id,
            "date_from": fields.Date.today(),
        })
        alloc.action_confirm()
        self.assertEqual(alloc.state, "confirmed")
        alloc.action_vacate()
        self.assertEqual(alloc.state, "vacated")
        self.assertEqual(self.room.state, "available")

    # ── Duplicate allocation raises UserError ─────────────────────────────

    def test_duplicate_allocation_raises(self):
        """Confirming a second allocation for the same student should raise UserError."""
        alloc1 = self.env["edu.hostel.allocation"].create({
            "enrollment_id": self.enrollment.id,
            "room_id": self.room.id,
            "date_from": fields.Date.today(),
        })
        alloc1.action_confirm()

        # Create a second room so the room-availability is not the blocker
        room2 = self.env["edu.hostel.room"].create({
            "property_id": self.property.id,
            "room_no": "102",
            "room_type": "single",
            "capacity": 1,
            "state": "available",
        })
        alloc2 = self.env["edu.hostel.allocation"].create({
            "enrollment_id": self.enrollment.id,
            "room_id": room2.id,
            "date_from": fields.Date.today(),
        })
        with self.assertRaises(UserError):
            alloc2.action_confirm()

        # Clean up
        alloc1.action_vacate()

    # ── Date constraint ───────────────────────────────────────────────────

    def test_date_constraint(self):
        """date_to earlier than date_from should raise ValidationError."""
        with self.assertRaises(ValidationError):
            self.env["edu.hostel.allocation"].create({
                "enrollment_id": self.enrollment.id,
                "room_id": self.room.id,
                "date_from": fields.Date.today(),
                "date_to": fields.Date.today() - timedelta(days=1),
            })

    # ── Property computed counts ──────────────────────────────────────────

    def test_room_counts(self):
        """property.room_count should be 1; occupied_count should be 1 after confirming an allocation."""
        # Ensure the room we created in setUpClass is available
        self.room.state = "available"
        self.property._compute_room_counts()
        # room_count counts ALL rooms linked to this property (at least 1)
        self.assertGreaterEqual(self.property.room_count, 1)

        alloc = self.env["edu.hostel.allocation"].create({
            "enrollment_id": self.enrollment.id,
            "room_id": self.room.id,
            "date_from": fields.Date.today(),
        })
        alloc.action_confirm()
        self.property._compute_room_counts()
        self.assertGreaterEqual(self.property.occupied_count, 1)

        # Clean up
        alloc.action_vacate()
