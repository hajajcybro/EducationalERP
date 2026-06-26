# -*- coding: utf-8 -*-
"""
education_transport — Unit Tests
==================================
Covers:
  - Route stop_count computed field
  - Transport assignment default state
  - Unique assignment constraint (same enrollment + year)
  - Fleet vehicle <-> route integration (school vehicles)
"""
from datetime import date, timedelta

from odoo.tests import TransactionCase, tagged
from odoo.exceptions import ValidationError, UserError
from odoo import fields


@tagged("post_install", "-at_install")
class TestTransport(TransactionCase):
    """Unit tests for the education_transport module."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # ── Route & stop ──────────────────────────────────────────────────
        cls.route = cls.env["edu.transport.route"].create({
            "name": "Route 1",
        })
        cls.stop = cls.env["edu.transport.stop"].create({
            "name": "Main Gate",
            "route_id": cls.route.id,
            "sequence": 10,
        })

        # ── Academic year ─────────────────────────────────────────────────
        cls.academic_year = cls.env["education.academic.year"].create({
            "name": "Transport Test Year",
            "code": "TRNYR26",
            "date_start": date(2025, 7, 1),
            "date_end": date(2026, 6, 30),
            "is_current": False,
        })

        # ── Enrollment (via application workflow) ─────────────────────────
        cls.department = cls.env["education.department"].create({
            "name": "Transport Test Dept",
            "code": "TRNDEPT",
        })
        cls.program = cls.env["education.program"].create({
            "name": "Transport Test Program",
            "code": "TRNPROG",
            "department_id": cls.department.id,
            "degree_type": "bachelor",
            "duration_years": 3,
        })
        app = cls.env["education.application"].create({
            "first_name": "Diana",
            "last_name": "TransportStudent",
            "date_of_birth": date.today() - timedelta(days=365 * 18),
            "gender": "female",
            "email": "diana.transport@example.com",
            "phone": "4444444444",
            "program_id": cls.program.id,
            "academic_year_id": cls.academic_year.id,
        })
        app.action_submit()
        app.action_approve()
        cls.enrollment = app.enrollment_id

    # ── Stop count ────────────────────────────────────────────────────────

    def test_route_stop_count(self):
        """route.stop_count should equal the number of linked stops."""
        self.route._compute_stop_count()
        self.assertEqual(self.route.stop_count, 1)

    # ── Assignment created with default state ─────────────────────────────

    def test_assignment_created(self):
        """A newly created transport assignment should have state='active'."""
        assignment = self.env["edu.transport.assignment"].create({
            "enrollment_id": self.enrollment.id,
            "route_id": self.route.id,
            "stop_id": self.stop.id,
            "academic_year_id": self.academic_year.id,
        })
        self.assertEqual(assignment.state, "active")
        # Clean up to avoid interference with other tests
        assignment.unlink()

    # ── Unique assignment constraint ──────────────────────────────────────

    def test_unique_assignment(self):
        """Creating two assignments for the same enrollment+year should raise an IntegrityError."""
        from psycopg2 import IntegrityError as Psycopg2IntegrityError

        assignment1 = self.env["edu.transport.assignment"].create({
            "enrollment_id": self.enrollment.id,
            "route_id": self.route.id,
            "stop_id": self.stop.id,
            "academic_year_id": self.academic_year.id,
        })

        with self.assertRaises(Exception):
            # Odoo wraps the psycopg2 IntegrityError; catching the base
            # Exception covers both the raw error and any Odoo wrapper.
            with self.env.cr.savepoint():
                self.env["edu.transport.assignment"].create({
                    "enrollment_id": self.enrollment.id,
                    "route_id": self.route.id,
                    "stop_id": self.stop.id,
                    "academic_year_id": self.academic_year.id,
                })

        # Clean up
        assignment1.unlink()

    # ── Fleet vehicle <-> route integration ──────────────────────────────

    def test_school_vehicle_route_link(self):
        """A fleet.vehicle flagged as a school vehicle should attach to its route."""
        brand = self.env["fleet.vehicle.model.brand"].create({"name": "Tata"})
        model = self.env["fleet.vehicle.model"].create({
            "name": "Starbus",
            "brand_id": brand.id,
        })
        vehicle = self.env["fleet.vehicle"].create({
            "model_id": model.id,
            "license_plate": "KL-01-TEST-9999",
            "is_school_vehicle": True,
            "condition": "good",
            "route_id": self.route.id,
        })

        self.assertIn(vehicle, self.route.vehicle_ids)
        self.route._compute_vehicle_count()
        self.assertEqual(self.route.vehicle_count, 1)
