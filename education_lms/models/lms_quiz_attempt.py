# -*- coding: utf-8 -*-
"""
LMS Quiz Attempt model (S7-T05)
================================
edu.lms.quiz.attempt — records each student attempt at a quiz,
stores answers as JSON, computes score, pass/fail and percentage.
"""
from odoo import models, fields, api


class EduLmsQuizAttempt(models.Model):
    """A single student attempt at an LMS quiz."""

    _name = "edu.lms.quiz.attempt"
    _description = "LMS Quiz Attempt"
    _order = "attempt_date desc, id desc"
    _rec_name = "quiz_id"

    student_id = fields.Many2one(
        "education.enrollment",
        string="Student",
        required=True,
        ondelete="restrict",
        index=True,
    )
    quiz_id = fields.Many2one(
        "edu.lms.quiz",
        string="Quiz",
        required=True,
        ondelete="restrict",
        index=True,
    )
    # JSON-encoded answers stored as Char
    answers = fields.Char(
        string="Answers (JSON)",
        help="JSON object mapping question IDs to submitted answers.",
    )
    score = fields.Float(string="Score", default=0.0)
    max_score = fields.Float(
        string="Max Score",
        compute="_compute_max_score",
        store=True,
    )
    passed = fields.Boolean(
        string="Passed",
        compute="_compute_passed",
        store=True,
    )
    percentage = fields.Float(
        string="Percentage (%)",
        compute="_compute_percentage",
        store=True,
        digits=(5, 2),
    )
    attempt_date = fields.Datetime(
        string="Attempt Date",
        default=fields.Datetime.now,
        required=True,
    )
    attempt_number = fields.Integer(string="Attempt #", default=1)

    # ── Computed ─────────────────────────────────────────────────────────
    @api.depends("quiz_id", "quiz_id.question_ids", "quiz_id.question_ids.marks")
    def _compute_max_score(self):
        for rec in self:
            rec.max_score = sum(rec.quiz_id.question_ids.mapped("marks"))

    @api.depends("score", "quiz_id.pass_marks")
    def _compute_passed(self):
        for rec in self:
            if rec.max_score:
                pct = (rec.score / rec.max_score) * 100.0
            else:
                pct = 0.0
            rec.passed = pct >= rec.quiz_id.pass_marks

    @api.depends("score", "max_score")
    def _compute_percentage(self):
        for rec in self:
            if rec.max_score:
                rec.percentage = (rec.score / rec.max_score) * 100.0
            else:
                rec.percentage = 0.0
