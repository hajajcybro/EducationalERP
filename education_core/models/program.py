# -*- coding: utf-8 -*-
"""education.program — Academic program / course of study model."""
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class EducationProgram(models.Model):
    """
    Academic program offered by a department (e.g. B.Tech CSE, MBA, MBBS).
    Programs group into classes/sections per academic year.
    """

    _name = "education.program"
    _description = "Academic Program"
    _order = "department_id, name"
    _inherit = ["mail.thread"]
    _rec_name = "full_name"

    # ── Identity ─────────────────────────────────────────────────────────
    name = fields.Char(
        string="Program Name",
        required=True,
        tracking=True,
        translate=True,
        help="Full name, e.g. Bachelor of Technology — Computer Science.",
    )
    code = fields.Char(
        string="Program Code",
        required=True,
        size=20,
        tracking=True,
        help="Short code used in class names and sequences (e.g. BTECH-CSE).",
    )
    full_name = fields.Char(
        string="Display Name",
        compute="_compute_full_name",
        store=True,
        help="Code + Name used as _rec_name.",
    )
    degree_type = fields.Selection(
        selection=[
            ("certificate", "Certificate"),
            ("diploma", "Diploma"),
            ("bachelor", "Bachelor's Degree"),
            ("master", "Master's Degree"),
            ("phd", "PhD / Doctorate"),
            ("professional", "Professional Degree (MBBS, LLB, etc.)"),
            ("vocational", "Vocational / Trade"),
            ("corporate", "Corporate Training"),
            ("other", "Other"),
        ],
        string="Degree Type",
        required=True,
        default="bachelor",
        tracking=True,
    )
    duration_years = fields.Integer(
        string="Duration (Years)",
        required=True,
        default=3,
        help="Total number of academic years to complete this program.",
    )
    semesters_per_year = fields.Integer(
        string="Semesters per Year",
        default=2,
    )

    # ── Relationships ─────────────────────────────────────────────────────
    department_id = fields.Many2one(
        "education.department",
        string="Department",
        required=True,
        tracking=True,
        ondelete="restrict",
        index=True,
    )
    class_ids = fields.One2many(
        "education.class",
        "program_id",
        string="Classes",
    )
    class_count = fields.Integer(
        string="# Classes",
        compute="_compute_class_count",
    )

    # ── Description ───────────────────────────────────────────────────────
    description = fields.Html(
        string="Program Description",
        sanitize=True,
    )
    eligibility = fields.Text(
        string="Eligibility / Entry Requirements",
    )

    # ── System ────────────────────────────────────────────────────────────
    sequence = fields.Integer(default=10)
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        default=lambda self: self.env.company,
        required=True,
        index=True,
    )
    active = fields.Boolean(default=True)

    _sql_constraints = [
        (
            "code_company_uniq",
            "UNIQUE(code, company_id)",
            "Program code must be unique per company.",
        )
    ]

    # ── Constraints ────────────────────────────────────────────────────────

    @api.constrains("duration_years")
    def _check_duration(self):
        for rec in self:
            if rec.duration_years < 1:
                raise ValidationError(
                    _("Program duration must be at least 1 year.")
                )

    # ── Computed ───────────────────────────────────────────────────────────

    @api.depends("code", "name")
    def _compute_full_name(self):
        for rec in self:
            rec.full_name = f"[{rec.code}] {rec.name}" if rec.code else rec.name

    @api.depends("class_ids")
    def _compute_class_count(self):
        for rec in self:
            rec.class_count = len(rec.class_ids)

    # ── Actions ────────────────────────────────────────────────────────────

    def action_view_classes(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Classes — %s") % self.full_name,
            "res_model": "education.class",
            "domain": [("program_id", "=", self.id)],
            "view_mode": "list,form",
            "context": {"default_program_id": self.id},
        }
