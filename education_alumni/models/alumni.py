# -*- coding: utf-8 -*-
"""
edu.alumni — Alumni Profile
============================
One record per graduated enrollment; tracks professional and contact
information for alumni engagement.

Sprint 7 — Task 17
"""
from odoo import models, fields


class EduAlumni(models.Model):
    """Alumni profile linked to a single student enrollment."""

    _name = "edu.alumni"
    _description = "Alumni"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _rec_name = "student_name"
    _order = "graduation_year desc, student_name"

    # ── Enrollment link ──────────────────────────────────────────────────
    enrollment_id = fields.Many2one(
        "education.enrollment",
        string="Enrollment",
        required=True,
        ondelete="restrict",
        index=True,
        tracking=True,
    )

    # ── Graduation info ──────────────────────────────────────────────────
    graduation_year = fields.Integer(
        string="Graduation Year",
        required=True,
        tracking=True,
    )
    graduation_date = fields.Date(
        string="Graduation Date",
        tracking=True,
    )

    # ── Related fields from enrollment ──────────────────────────────────
    program_id = fields.Many2one(
        "education.program",
        string="Program",
        related="enrollment_id.program_id",
        store=True,
        readonly=True,
    )
    student_name = fields.Char(
        string="Student Name",
        related="enrollment_id.student_name",
        store=True,
        readonly=True,
    )

    # ── Professional info ────────────────────────────────────────────────
    current_employer = fields.Char(string="Current Employer")
    job_title = fields.Char(string="Job Title")

    # ── Contact info ─────────────────────────────────────────────────────
    contact_email = fields.Char(string="Contact Email")
    contact_phone = fields.Char(string="Contact Phone")
    linkedin_url = fields.Char(string="LinkedIn URL")
    address = fields.Text(string="Address")

    # ── Misc ─────────────────────────────────────────────────────────────
    notes = fields.Text(string="Notes")
    active = fields.Boolean(string="Active", default=True)

    # ── Constraints ──────────────────────────────────────────────────────
    _sql_constraints = [
        (
            "enrollment_unique",
            "UNIQUE(enrollment_id)",
            "An alumni record already exists for this enrollment.",
        ),
    ]
