# -*- coding: utf-8 -*-
"""
education.leave.request — Student leave application with approval (S3-T03)
===========================================================================
Students (or guardians) apply for leave; admin/teacher approves/rejects.
Approved leaves auto-mark attendance as 'excused' for the covered dates.
"""
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class EducationLeaveRequest(models.Model):
    """Student leave request — applies for excused absence."""

    _name = "education.leave.request"
    _description = "Student Leave Request"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "date_from desc"
    _rec_name = "reference"

    reference = fields.Char(
        string="Reference",
        readonly=True,
        copy=False,
        default="New",
    )
    state = fields.Selection(
        selection=[
            ("draft", "Draft"),
            ("submitted", "Submitted"),
            ("approved", "Approved"),
            ("rejected", "Rejected"),
        ],
        string="Status",
        default="draft",
        required=True,
        tracking=True,
    )

    # ── Student ───────────────────────────────────────────────────────────
    enrollment_id = fields.Many2one(
        "education.enrollment",
        string="Student Enrollment",
        required=True,
        ondelete="restrict",
        index=True,
    )
    student_name = fields.Char(
        related="enrollment_id.student_name",
        store=True,
        readonly=True,
    )
    class_id = fields.Many2one(
        "education.class",
        related="enrollment_id.class_id",
        store=True,
        readonly=True,
    )

    # ── Leave Details ─────────────────────────────────────────────────────
    date_from = fields.Date(string="From Date", required=True)
    date_to = fields.Date(string="To Date", required=True)
    days_count = fields.Integer(
        string="Days",
        compute="_compute_days_count",
        store=True,
    )
    leave_type = fields.Selection(
        selection=[
            ("medical", "Medical / Sick Leave"),
            ("personal", "Personal"),
            ("family", "Family Emergency"),
            ("event", "Participation in Event"),
            ("other", "Other"),
        ],
        string="Leave Type",
        required=True,
        default="personal",
    )
    reason = fields.Text(string="Reason", required=True)
    supporting_document = fields.Binary(
        string="Supporting Document",
        attachment=True,
        help="Medical certificate, event permission letter, etc.",
    )
    supporting_document_name = fields.Char()

    # ── Approval ──────────────────────────────────────────────────────────
    approved_by_id = fields.Many2one(
        "res.users",
        string="Approved / Rejected By",
        readonly=True,
    )
    approval_date = fields.Date(string="Decision Date", readonly=True)
    rejection_reason = fields.Text(string="Rejection Reason", readonly=True)

    # ── System ────────────────────────────────────────────────────────────
    company_id = fields.Many2one(
        "res.company",
        related="enrollment_id.company_id",
        store=True,
        readonly=True,
    )

    # ── ORM ───────────────────────────────────────────────────────────────

    @api.model_create_multi
    def create(self, vals_list):
        Seq = self.env["ir.sequence"]
        for vals in vals_list:
            if vals.get("reference", "New") == "New":
                vals["reference"] = Seq.next_by_code("education.leave.request") or "New"
        return super().create(vals_list)

    # ── Computed ───────────────────────────────────────────────────────────

    @api.depends("date_from", "date_to")
    def _compute_days_count(self):
        for rec in self:
            if rec.date_from and rec.date_to:
                delta = rec.date_to - rec.date_from
                rec.days_count = max(1, delta.days + 1)
            else:
                rec.days_count = 0

    # ── Constraints ────────────────────────────────────────────────────────

    @api.constrains("date_from", "date_to")
    def _check_dates(self):
        for rec in self:
            if rec.date_from and rec.date_to and rec.date_to < rec.date_from:
                raise ValidationError(
                    _("To Date must be on or after From Date.")
                )

    # ── State Machine ──────────────────────────────────────────────────────

    def action_submit(self):
        self.filtered(lambda r: r.state == "draft").write({"state": "submitted"})

    def action_approve(self):
        """Approve and mark attendance as excused for covered periods."""
        for rec in self.filtered(lambda r: r.state == "submitted"):
            rec.write({
                "state": "approved",
                "approved_by_id": self.env.uid,
                "approval_date": fields.Date.today(),
            })
            # Excused absent attendance records
            rec._mark_attendance_excused()
            rec.message_post(
                body=_("Leave approved for %s to %s (%d day(s)).")
                % (rec.date_from, rec.date_to, rec.days_count)
            )

    def action_reject(self):
        self.filtered(lambda r: r.state == "submitted").write({
            "state": "rejected",
            "approved_by_id": self.env.uid,
            "approval_date": fields.Date.today(),
        })

    def action_reset_draft(self):
        self.filtered(lambda r: r.state == "rejected").write({"state": "draft"})

    def _mark_attendance_excused(self):
        """Mark all absence records in the leave period as 'excused'."""
        self.ensure_one()
        attendance = self.env["education.attendance"].search([
            ("enrollment_id", "=", self.enrollment_id.id),
            ("date", ">=", self.date_from),
            ("date", "<=", self.date_to),
            ("state", "=", "absent"),
        ])
        attendance.write({"state": "excused"})
