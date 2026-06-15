# -*- coding: utf-8 -*-
"""
edu.exam — Exam scheduling (S4-T01)
====================================
Header record for an examination event.
Holds dates, linked classes, subject schedule lines, seating, invigilators
and a state machine: draft → scheduled → ongoing → result_published → closed.
"""
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class EduExam(models.Model):
    """Exam header — one exam event (e.g. Mid-Term Nov 2026)."""

    _name = "edu.exam"
    _description = "Examination"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "date_from desc, id desc"
    _rec_name = "name"

    # ── Identity ──────────────────────────────────────────────────────────
    name = fields.Char(
        string="Exam Name",
        required=True,
        tracking=True,
    )
    code = fields.Char(
        string="Exam Code",
        readonly=True,
        copy=False,
        default="New",
    )
    exam_type = fields.Selection(
        selection=[
            ("unit_test", "Unit Test"),
            ("mid_term", "Mid-Term"),
            ("final", "Final Exam"),
            ("practical", "Practical"),
            ("supplementary", "Supplementary"),
        ],
        string="Exam Type",
        required=True,
        default="mid_term",
        tracking=True,
    )
    state = fields.Selection(
        selection=[
            ("draft", "Draft"),
            ("scheduled", "Scheduled"),
            ("ongoing", "Ongoing"),
            ("result_published", "Results Published"),
            ("closed", "Closed"),
        ],
        string="Status",
        default="draft",
        required=True,
        tracking=True,
    )

    # ── Dates & Scope ─────────────────────────────────────────────────────
    academic_year_id = fields.Many2one(
        "education.academic.year",
        string="Academic Year",
        required=True,
        index=True,
    )
    date_from = fields.Date(
        string="Start Date",
        required=True,
    )
    date_to = fields.Date(
        string="End Date",
        required=True,
    )
    class_ids = fields.Many2many(
        "education.class",
        "edu_exam_class_rel",
        "exam_id",
        "class_id",
        string="Classes",
    )

    # ── Related lines ─────────────────────────────────────────────────────
    subject_line_ids = fields.One2many(
        "edu.exam.subject",
        "exam_id",
        string="Subject Schedule",
    )
    seating_ids = fields.One2many(
        "edu.exam.seating",
        "exam_id",
        string="Seating Plan",
    )
    invigilator_ids = fields.One2many(
        "edu.exam.invigilator",
        "exam_id",
        string="Invigilators",
    )
    result_ids = fields.One2many(
        "edu.exam.result",
        "exam_id",
        string="Results",
    )

    # ── Stats ─────────────────────────────────────────────────────────────
    subject_count = fields.Integer(
        compute="_compute_counts",
        string="Subjects",
    )
    seating_count = fields.Integer(
        compute="_compute_counts",
        string="Seats Assigned",
    )
    result_count = fields.Integer(
        compute="_compute_counts",
        string="Results",
    )

    notes = fields.Text(string="Instructions / Notes")
    company_id = fields.Many2one(
        "res.company",
        default=lambda self: self.env.company,
        readonly=True,
    )

    # ── ORM ───────────────────────────────────────────────────────────────

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("code", "New") == "New":
                vals["code"] = (
                    self.env["ir.sequence"].next_by_code("edu.exam") or "New"
                )
        return super().create(vals_list)

    # ── Computed ──────────────────────────────────────────────────────────

    @api.depends("subject_line_ids", "seating_ids", "result_ids")
    def _compute_counts(self):
        for rec in self:
            rec.subject_count = len(rec.subject_line_ids)
            rec.seating_count = len(rec.seating_ids)
            rec.result_count = len(rec.result_ids)

    # ── Constraints ───────────────────────────────────────────────────────

    @api.constrains("date_from", "date_to")
    def _check_dates(self):
        for rec in self:
            if rec.date_from and rec.date_to and rec.date_to < rec.date_from:
                raise ValidationError(
                    _("End Date must be on or after Start Date.")
                )

    # ── State machine ─────────────────────────────────────────────────────

    def action_schedule(self):
        for rec in self.filtered(lambda r: r.state == "draft"):
            if not rec.subject_line_ids:
                raise UserError(
                    _("Add at least one subject before scheduling exam '%s'.") % rec.name
                )
            rec.write({"state": "scheduled"})

    def action_start(self):
        self.filtered(lambda r: r.state == "scheduled").write({"state": "ongoing"})

    def action_publish_results(self):
        for rec in self.filtered(lambda r: r.state == "ongoing"):
            if not rec.result_ids:
                raise UserError(
                    _("No results entered for exam '%s'.") % rec.name
                )
            rec.result_ids.filtered(
                lambda r: r.state == "draft"
            ).write({"state": "published"})
            rec.write({"state": "result_published"})
            rec.message_post(
                body=_("Results published for %d students.") % len(rec.result_ids)
            )

    def action_close(self):
        self.filtered(
            lambda r: r.state == "result_published"
        ).write({"state": "closed"})

    def action_reset_draft(self):
        self.filtered(lambda r: r.state != "closed").write({"state": "draft"})

    # ── Seating plan generation ────────────────────────────────────────────

    def action_generate_seating(self):
        """Auto-generate seating assignments for all enrolled students."""
        self.ensure_one()
        if not self.class_ids:
            raise UserError(_("No classes linked to this exam."))

        # Remove existing seating
        self.seating_ids.unlink()

        Seating = self.env["edu.exam.seating"]
        enrollments = self.env["education.enrollment"].search([
            ("class_id", "in", self.class_ids.ids),
            ("state", "=", "active"),
        ], order="class_id, id")

        roll = 1
        for enr in enrollments:
            Seating.create({
                "exam_id": self.id,
                "enrollment_id": enr.id,
                "roll_no": str(roll).zfill(4),
            })
            roll += 1

        self.message_post(
            body=_("Seating plan generated for %d students.") % len(enrollments)
        )
        return {
            "type": "ir.actions.act_window",
            "name": _("Seating Plan"),
            "res_model": "edu.exam.seating",
            "view_mode": "list",
            "domain": [("exam_id", "=", self.id)],
        }


class EduExamSubject(models.Model):
    """One subject (paper) within an exam — date, time, marks, room."""

    _name = "edu.exam.subject"
    _description = "Exam Subject Schedule"
    _order = "exam_date, exam_time"

    exam_id = fields.Many2one(
        "edu.exam",
        string="Exam",
        required=True,
        ondelete="cascade",
        index=True,
    )
    subject = fields.Char(
        string="Subject / Paper",
        required=True,
    )
    exam_date = fields.Date(string="Date")
    exam_time = fields.Float(
        string="Start Time",
        help="24-hour format, e.g. 9.5 = 09:30",
    )
    duration_hours = fields.Float(
        string="Duration (hrs)",
        default=3.0,
    )
    max_marks = fields.Float(
        string="Max Marks",
        required=True,
        default=100.0,
    )
    pass_marks = fields.Float(
        string="Pass Marks",
        required=True,
        default=40.0,
    )
    classroom_id = fields.Many2one(
        "edu.classroom",
        string="Exam Hall",
    )

    @api.constrains("pass_marks", "max_marks")
    def _check_marks(self):
        for rec in self:
            if rec.pass_marks > rec.max_marks:
                raise ValidationError(
                    _("Pass marks cannot exceed max marks for subject '%s'.") % rec.subject
                )
            if rec.max_marks <= 0:
                raise ValidationError(_("Max marks must be greater than zero."))
