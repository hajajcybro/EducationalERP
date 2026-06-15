# -*- coding: utf-8 -*-
"""
edu.exam.result — Mark entry, grade computation, rank (S4-T04, S4-T05)
=======================================================================
One result record per student per subject per exam.
Grade, percentage, pass/fail and class rank are all computed fields.
Every marks change is recorded in edu.exam.result.history.
"""
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


# ── Grade helper ──────────────────────────────────────────────────────────

def _compute_grade(percentage):
    """Return letter grade from percentage score."""
    if percentage >= 90:
        return "A+"
    elif percentage >= 80:
        return "A"
    elif percentage >= 70:
        return "B"
    elif percentage >= 60:
        return "C"
    elif percentage >= 50:
        return "D"
    else:
        return "F"


class EduExamResult(models.Model):
    """Single exam result: one student, one subject, one exam."""

    _name = "edu.exam.result"
    _description = "Exam Result"
    _order = "exam_id, class_id, student_name, subject"
    _rec_name = "display_name"

    display_name = fields.Char(
        compute="_compute_display_name",
        store=True,
    )

    # ── Core links ────────────────────────────────────────────────────────
    exam_id = fields.Many2one(
        "edu.exam",
        string="Exam",
        required=True,
        ondelete="cascade",
        index=True,
    )
    enrollment_id = fields.Many2one(
        "education.enrollment",
        string="Student",
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
    roll_no = fields.Char(
        string="Roll No.",
        compute="_compute_roll_no",
        store=True,
        readonly=True,
    )
    subject = fields.Char(
        string="Subject",
        required=True,
    )

    # ── Marks ─────────────────────────────────────────────────────────────
    marks_obtained = fields.Float(
        string="Marks Obtained",
        default=0.0,
        tracking=True,
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

    # ── Computed grade fields ─────────────────────────────────────────────
    percentage = fields.Float(
        string="Percentage (%)",
        compute="_compute_grade_fields",
        store=True,
        digits=(5, 2),
    )
    grade = fields.Char(
        string="Grade",
        compute="_compute_grade_fields",
        store=True,
    )
    pass_fail = fields.Selection(
        selection=[
            ("pass", "Pass"),
            ("fail", "Fail"),
            ("absent", "Absent"),
        ],
        string="Result",
        compute="_compute_grade_fields",
        store=True,
    )
    rank = fields.Integer(
        string="Rank",
        compute="_compute_rank",
        store=True,
        help="Rank within the same exam, class and subject.",
    )

    # ── Status ────────────────────────────────────────────────────────────
    state = fields.Selection(
        selection=[
            ("draft", "Draft"),
            ("published", "Published"),
        ],
        string="Status",
        default="draft",
        required=True,
        tracking=True,
    )
    absent = fields.Boolean(
        string="Absent",
        default=False,
        help="Check if student was absent for this paper.",
    )

    history_ids = fields.One2many(
        "edu.exam.result.history",
        "result_id",
        string="Change History",
    )
    history_count = fields.Integer(
        compute="_compute_history_count",
    )

    _sql_constraints = [
        (
            "exam_enrollment_subject_uniq",
            "UNIQUE(exam_id, enrollment_id, subject)",
            "A result for this student and subject already exists in this exam.",
        )
    ]

    # ── ORM override — track marks changes ────────────────────────────────

    def write(self, vals):
        if "marks_obtained" in vals:
            for rec in self:
                old = rec.marks_obtained
                new = vals["marks_obtained"]
                if old != new:
                    self.env["edu.exam.result.history"].create({
                        "result_id": rec.id,
                        "old_marks": old,
                        "new_marks": new,
                        "changed_by_id": self.env.uid,
                        "change_date": fields.Datetime.now(),
                        "reason": vals.get("_change_reason", ""),
                    })
        return super().write(vals)

    # ── Computed ──────────────────────────────────────────────────────────

    @api.depends("enrollment_id", "exam_id")
    def _compute_roll_no(self):
        for rec in self:
            seating = self.env["edu.exam.seating"].search([
                ("exam_id", "=", rec.exam_id.id),
                ("enrollment_id", "=", rec.enrollment_id.id),
            ], limit=1)
            rec.roll_no = seating.roll_no if seating else ""

    @api.depends("marks_obtained", "max_marks", "pass_marks", "absent")
    def _compute_grade_fields(self):
        for rec in self:
            if rec.absent:
                rec.percentage = 0.0
                rec.grade = "AB"
                rec.pass_fail = "absent"
                continue
            if rec.max_marks:
                pct = (rec.marks_obtained / rec.max_marks) * 100
            else:
                pct = 0.0
            rec.percentage = pct
            rec.grade = _compute_grade(pct)
            rec.pass_fail = (
                "pass" if rec.marks_obtained >= rec.pass_marks else "fail"
            )

    @api.depends("exam_id", "class_id", "subject", "marks_obtained", "absent")
    def _compute_rank(self):
        """Rank within exam + class + subject, highest marks = rank 1."""
        # Group results by (exam_id, class_id, subject)
        groups = {}
        for rec in self:
            key = (rec.exam_id.id, rec.class_id.id, rec.subject)
            groups.setdefault(key, []).append(rec)

        for key, records in groups.items():
            # Sort: absent last, then by marks descending
            sorted_recs = sorted(
                records,
                key=lambda r: (-r.marks_obtained if not r.absent else -9999),
            )
            rank = 1
            for r in sorted_recs:
                r.rank = rank if not r.absent else 0
                rank += 1

    @api.depends("student_name", "subject", "exam_id")
    def _compute_display_name(self):
        for rec in self:
            rec.display_name = (
                f"{rec.student_name or '?'} / {rec.subject or '?'}"
            )

    @api.depends("history_ids")
    def _compute_history_count(self):
        for rec in self:
            rec.history_count = len(rec.history_ids)

    # ── Constraints ───────────────────────────────────────────────────────

    @api.constrains("marks_obtained", "max_marks")
    def _check_marks(self):
        for rec in self:
            if not rec.absent:
                if rec.marks_obtained < 0:
                    raise ValidationError(_("Marks obtained cannot be negative."))
                if rec.marks_obtained > rec.max_marks:
                    raise ValidationError(
                        _(
                            "Marks obtained (%.1f) cannot exceed max marks (%.1f) "
                            "for %s — %s."
                        ) % (
                            rec.marks_obtained,
                            rec.max_marks,
                            rec.student_name,
                            rec.subject,
                        )
                    )


class EduExamResultHistory(models.Model):
    """Audit log — every marks change is recorded here (S4-T06)."""

    _name = "edu.exam.result.history"
    _description = "Exam Result Change History"
    _order = "change_date desc"

    result_id = fields.Many2one(
        "edu.exam.result",
        string="Result",
        required=True,
        ondelete="cascade",
        index=True,
    )
    old_marks = fields.Float(string="Old Marks")
    new_marks = fields.Float(string="New Marks")
    changed_by_id = fields.Many2one(
        "res.users",
        string="Changed By",
    )
    change_date = fields.Datetime(
        string="Changed On",
        default=fields.Datetime.now,
    )
    reason = fields.Text(string="Reason / Note")
    delta = fields.Float(
        string="Change",
        compute="_compute_delta",
        store=True,
    )

    @api.depends("old_marks", "new_marks")
    def _compute_delta(self):
        for rec in self:
            rec.delta = rec.new_marks - rec.old_marks
