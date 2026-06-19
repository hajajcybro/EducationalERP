# -*- coding: utf-8 -*-
"""education.academic.year — Academic year model."""
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class AcademicYear(models.Model):
    """
    Represents a single academic year (e.g. 2025-2026).
    Exactly one record should have is_current=True per company.
    """

    _name = "education.academic.year"
    _description = "Academic Year"
    _order = "date_start desc"
    _inherit = ["mail.thread"]

    name = fields.Char(
        string="Academic Year",
        required=True,
        tracking=True,
        help='e.g. "2025-2026" or "Spring 2026".',
    )
    code = fields.Char(
        string="Code",
        required=True,
        size=10,
        help='Short code used in sequence prefixes (e.g. "AY2526").',
    )
    date_start = fields.Date(
        string="Start Date",
        required=True,
        tracking=True,
    )
    date_end = fields.Date(
        string="End Date",
        required=True,
        tracking=True,
    )
    is_current = fields.Boolean(
        string="Current Year",
        default=False,
        tracking=True,
        help="Mark the currently active academic year. "
             "Only one year can be current per company.",
    )
    sequence = fields.Integer(default=10)
    notes = fields.Text(string="Notes")
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        default=lambda self: self.env.company,
        required=True,
        index=True,
    )
    active = fields.Boolean(default=True)

    # ── Computed statistics ────────────────────────────────────────────────
    enrollment_count = fields.Integer(
        string="Enrollments",
        compute="_compute_enrollment_count",
    )

    @api.constrains("date_start", "date_end")
    def _check_dates(self):
        for rec in self:
            if rec.date_end <= rec.date_start:
                raise ValidationError(
                    _("End Date must be after Start Date for academic year '%s'.")
                    % rec.name
                )

    @api.constrains("is_current", "company_id")
    def _check_single_current(self):
        for rec in self:
            if rec.is_current:
                others = self.search([
                    ("is_current", "=", True),
                    ("company_id", "=", rec.company_id.id),
                    ("id", "!=", rec.id),
                ])
                if others:
                    raise ValidationError(
                        _("Only one Academic Year can be marked as current per company. "
                          "'%s' is already set as current.") % others[0].name
                    )

    # ── Compute ────────────────────────────────────────────────────────────

    def _compute_enrollment_count(self):
        """Count active enrollments for this academic year."""
        Enrollment = self.env["education.enrollment"]
        for rec in self:
            rec.enrollment_count = Enrollment.search_count([
                ("academic_year_id", "=", rec.id),
                ("state", "=", "active"),
            ])

    # ── Business Methods ───────────────────────────────────────────────────

    def action_set_current(self):
        """Mark this year as current, unset all others for this company."""
        self.ensure_one()
        self.search([
            ("company_id", "=", self.company_id.id),
            ("id", "!=", self.id),
        ]).write({"is_current": False})
        self.write({"is_current": True})

    @api.model
    def get_current_year(self):
        """Return the current academic year for this company, or False."""
        return self.search(
            [("is_current", "=", True), ("company_id", "=", self.env.company.id)],
            limit=1,
        )
