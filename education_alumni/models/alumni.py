# -*- coding: utf-8 -*-
"""
edu.alumni — Alumni Profile
============================
One record per graduated enrollment; tracks professional and contact
information for alumni engagement.

Sprint 7 — Task 17
"""
from dateutil.relativedelta import relativedelta

from odoo import api, models, fields


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

    # ── Graduation info (auto-derived from the student's enrollment) ─────
    graduation_date = fields.Date(
        string="Graduation Date",
        compute="_compute_graduation",
        store=True,
        readonly=True,
        tracking=True,
        help="Expected graduation date, derived from the enrollment's "
             "academic year and the program duration.",
    )
    graduation_year = fields.Integer(
        string="Graduation Year",
        compute="_compute_graduation",
        store=True,
        readonly=True,
        tracking=True,
        help="Computed from the graduation date.",
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

    # ── Compute ──────────────────────────────────────────────────────────
    @api.depends(
        "enrollment_id.academic_year_id.date_start",
        "enrollment_id.academic_year_id.date_end",
        "enrollment_id.program_id.duration_years",
    )
    def _compute_graduation(self):
        """Derive graduation date/year from the student's enrollment.

        A student enrolled in academic year *Y* on an *n*-year program is
        expected to graduate at the end of that program's final academic
        year, i.e. ``Y.date_end + (n - 1) years``.
        """
        for rec in self:
            academic_year = rec.enrollment_id.academic_year_id
            duration = rec.enrollment_id.program_id.duration_years or 0
            grad_date = False
            if academic_year.date_end and duration:
                grad_date = academic_year.date_end + relativedelta(
                    years=duration - 1
                )
            elif academic_year.date_start and duration:
                # Fallback when the academic year has no end date set.
                grad_date = academic_year.date_start + relativedelta(
                    years=duration
                )
            rec.graduation_date = grad_date
            rec.graduation_year = grad_date.year if grad_date else False

    # ── Constraints ──────────────────────────────────────────────────────
    _enrollment_unique = models.Constraint(
            "UNIQUE(enrollment_id)",
            "An alumni record already exists for this enrollment.",
        ),

