# -*- coding: utf-8 -*-
"""education.class — Class / Section model."""
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class EducationClass(models.Model):
    """
    A class is a specific section/batch of a program in a given academic year.
    Example: B.Tech CSE Section A — 2025-2026.

    Multiple classes can exist for the same program/year with different sections.
    """

    _name = "education.class"
    _description = "Class / Section"
    _order = "academic_year_id desc, program_id, section"
    _inherit = ["mail.thread"]
    # _rec_name defaults to "name" — we store the auto-generated label there.

    # ── Identity ─────────────────────────────────────────────────────────
    name = fields.Char(
        string="Class Name",
        compute="_compute_name",
        store=True,
        help="Auto-generated: Program Code + Section + Year, e.g. BTECH-CSE-A-2526.",
    )
    section = fields.Char(
        string="Section",
        required=True,
        default="A",
        size=5,
        help='Section identifier, e.g. "A", "B", "Morning", "Weekend".',
    )
    capacity = fields.Integer(
        string="Max Capacity",
        default=60,
        help="Maximum number of students allowed in this class.",
    )

    # ── Relationships ─────────────────────────────────────────────────────
    program_id = fields.Many2one(
        "education.program",
        string="Program",
        required=True,
        ondelete="restrict",
        tracking=True,
        index=True,
    )
    academic_year_id = fields.Many2one(
        "education.academic.year",
        string="Academic Year",
        required=True,
        ondelete="restrict",
        tracking=True,
        index=True,
        default=lambda self: self.env["education.academic.year"].get_current_year(),
    )
    department_id = fields.Many2one(
        "education.department",
        string="Department",
        related="program_id.department_id",
        store=True,
        readonly=True,
    )
    class_teacher_id = fields.Many2one(
        "res.partner",
        string="Class Teacher",
        domain="[('is_company', '=', False)]",
        tracking=True,
    )

    # ── Enrollment counters (populated in Sprint 2) ───────────────────────
    enrollment_count = fields.Integer(
        string="Enrolled Students",
        compute="_compute_enrollment_count",
        help="Number of active enrollments in this class.",
    )
    seats_available = fields.Integer(
        string="Seats Available",
        compute="_compute_seats_available",
    )

    # ── System ────────────────────────────────────────────────────────────
    notes = fields.Text(string="Notes")
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        related="program_id.company_id",
        store=True,
        readonly=True,
    )
    active = fields.Boolean(default=True)

    _sql_constraints = [
        (
            "program_year_section_uniq",
            "UNIQUE(program_id, academic_year_id, section)",
            "A class with the same program, academic year and section already exists.",
        )
    ]

    # ── Constraints ────────────────────────────────────────────────────────

    @api.constrains("capacity")
    def _check_capacity(self):
        for rec in self:
            if rec.capacity < 1:
                raise ValidationError(
                    _("Class capacity must be at least 1.")
                )

    # ── Computed ───────────────────────────────────────────────────────────

    @api.depends("program_id.code", "section", "academic_year_id.code")
    def _compute_name(self):
        for rec in self:
            parts = [
                rec.program_id.code or "",
                f"Sec-{rec.section}" if rec.section else "",
                rec.academic_year_id.code or "",
            ]
            rec.name = "-".join(p for p in parts if p)

    def _compute_enrollment_count(self):
        """Count active enrollments in this class."""
        Enrollment = self.env["education.enrollment"]
        for rec in self:
            rec.enrollment_count = Enrollment.search_count([
                ("class_id", "=", rec.id),
                ("state", "=", "active"),
            ])

    @api.depends("capacity", "enrollment_count")
    def _compute_seats_available(self):
        for rec in self:
            rec.seats_available = max(0, rec.capacity - rec.enrollment_count)

    # ── Actions ────────────────────────────────────────────────────────────

    def action_view_enrollments(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Enrollments — %s") % self.name,
            "res_model": "education.enrollment",
            "domain": [("class_id", "=", self.id)],
            "view_mode": "list,form",
            "context": {"default_class_id": self.id},
        }
