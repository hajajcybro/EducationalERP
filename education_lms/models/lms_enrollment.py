# -*- coding: utf-8 -*-
"""
LMS Enrollment model (S7-T04)
==============================
edu.lms.enrollment — links an education.enrollment (student) to a course,
tracks completion percentage and certificate issuance.
"""
from odoo import models, fields, api


class EduLmsEnrollment(models.Model):
    """LMS course enrollment for a student."""

    _name = "edu.lms.enrollment"
    _description = "LMS Enrollment"
    _order = "enrolled_date desc, id desc"
    _rec_name = "student_id"

    student_id = fields.Many2one(
        "education.enrollment",
        string="Student",
        required=True,
        ondelete="restrict",
        index=True,
    )
    course_id = fields.Many2one(
        "education.lms.course",
        string="Course",
        required=True,
        ondelete="restrict",
        index=True,
    )
    enrolled_date = fields.Date(
        string="Enrolled Date",
        default=fields.Date.today,
        required=True,
    )
    completion_pct = fields.Float(
        string="Completion (%)",
        compute="_compute_completion_pct",
        store=True,
        default=0.0,
        digits=(5, 2),
    )
    state = fields.Selection(
        selection=[
            ("enrolled", "Enrolled"),
            ("completed", "Completed"),
            ("dropped", "Dropped"),
        ],
        string="Status",
        default="enrolled",
        required=True,
        tracking=True,
    )
    certificate_issued = fields.Boolean(
        string="Certificate Issued",
        default=False,
    )

    _unique_student_course = models.Constraint(
            "UNIQUE(student_id, course_id)",
            "A student can only be enrolled once per course.",)


    # ── Computed ─────────────────────────────────────────────────────────
    @api.depends("course_id", "course_id.lesson_ids", "state")
    def _compute_completion_pct(self):
        """
        Completion percentage based on completed lesson progress records.
        Since a dedicated progress model is not yet implemented, we fall back to
        0.0 for enrolled/dropped and 100.0 for completed enrollments.
        Override this method (or add a lesson-progress model) to track granular
        per-lesson completion.
        """
        for rec in self:
            if rec.state == "completed":
                rec.completion_pct = 100.0
            else:
                total = len(rec.course_id.lesson_ids)
                if not total:
                    rec.completion_pct = 0.0
                else:
                    # No lesson-progress model yet — stays at 0 until completed
                    rec.completion_pct = 0.0

    # ── Actions ──────────────────────────────────────────────────────────
    def action_mark_complete(self):
        for rec in self:
            rec.write({"state": "completed", "completion_pct": 100.0})

    def action_drop(self):
        for rec in self:
            rec.state = "dropped"

    def action_print_certificate(self):
        self.ensure_one()
        return self.env.ref(
            "education_lms.action_report_lms_certificate"
        ).report_action(self)
