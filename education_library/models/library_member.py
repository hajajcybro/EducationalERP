# -*- coding: utf-8 -*-
"""
edu.library.member
==================
S6-T02: Library member model — links an enrolled student to the library.
"""
from odoo import models, fields, api, _


class EduLibraryMember(models.Model):
    """Library member — a registered borrower (enrolled student)."""

    _name = "edu.library.member"
    _description = "Library Member"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "member_no"
    _rec_name = "member_no"

    # ── Identity ─────────────────────────────────────────────────────────────
    enrollment_id = fields.Many2one(
        "education.enrollment",
        string="Enrollment",
        required=True,
        ondelete="restrict",
        index=True,
        tracking=True,
    )
    member_no = fields.Char(
        string="Member No.",
        readonly=True,
        copy=False,
        default="New",
        tracking=True,
    )

    # ── Borrowing rules ───────────────────────────────────────────────────────
    borrowing_limit = fields.Integer(
        string="Borrowing Limit",
        default=3,
        help="Maximum number of books that can be borrowed simultaneously.",
    )

    # ── Computed ──────────────────────────────────────────────────────────────
    active_loans_count = fields.Integer(
        string="Active Loans",
        compute="_compute_active_loans_count",
        store=True,
    )

    # ── Loans ─────────────────────────────────────────────────────────────────
    loan_ids = fields.One2many(
        "edu.library.loan",
        "member_id",
        string="Loans",
    )

    # ── Convenience related fields ────────────────────────────────────────────
    student_name = fields.Char(
        string="Student Name",
        related="enrollment_id.student_name",
        store=True,
        readonly=True,
    )
    student_email = fields.Char(
        string="Student Email",
        related="enrollment_id.student_email",
        store=True,
        readonly=True,
    )
    student_partner_id = fields.Many2one(
        "res.partner",
        string="Student Partner",
        related="enrollment_id.student_partner_id",
        store=True,
        readonly=True,
    )

    # ── System ────────────────────────────────────────────────────────────────
    active = fields.Boolean(default=True)
    notes = fields.Text(string="Notes")

    _enrollment_uniq = models.Constraint(
            "UNIQUE(enrollment_id)",
            "This student is already registered as a library member.",),


    # ── ORM ───────────────────────────────────────────────────────────────────

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("member_no", "New") == "New":
                vals["member_no"] = (
                    self.env["ir.sequence"].next_by_code("edu.library.member")
                    or "New"
                )
        return super().create(vals_list)

    # ── Computed ──────────────────────────────────────────────────────────────

    @api.depends("loan_ids", "loan_ids.state")
    def _compute_active_loans_count(self):
        for rec in self:
            rec.active_loans_count = len(
                rec.loan_ids.filtered(lambda l: l.state in ("issued", "overdue"))
            )
