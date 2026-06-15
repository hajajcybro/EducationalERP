# -*- coding: utf-8 -*-
"""
LMS Course models (S7-T01)
===========================
edu.lms.course.category  — simple category tag
education.lms.course     — course with lessons, quizzes and enrollments
"""
from odoo import models, fields, api, _


class EduLmsCourseCategory(models.Model):
    """Course category — flat taxonomy for grouping courses."""

    _name = "edu.lms.course.category"
    _description = "LMS Course Category"
    _order = "name"

    name = fields.Char(string="Category Name", required=True)

    course_ids = fields.One2many(
        "education.lms.course",
        "category_id",
        string="Courses",
    )
    course_count = fields.Integer(
        string="Courses",
        compute="_compute_course_count",
    )

    @api.depends("course_ids")
    def _compute_course_count(self):
        for rec in self:
            rec.course_count = len(rec.course_ids)


class EducationLmsCourse(models.Model):
    """LMS Course — top-level container for lessons, quizzes and enrollments."""

    _name = "education.lms.course"
    _description = "LMS Course"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "title"
    _rec_name = "title"

    # ── Core fields ──────────────────────────────────────────────────────
    title = fields.Char(
        string="Course Title",
        required=True,
        tracking=True,
    )
    description = fields.Html(string="Description")
    thumbnail = fields.Binary(string="Thumbnail", attachment=True)
    category_id = fields.Many2one(
        "edu.lms.course.category",
        string="Category",
        ondelete="set null",
    )
    teacher_id = fields.Many2one(
        "education.faculty",
        string="Teacher",
        ondelete="set null",
        tracking=True,
    )

    # ── State / mode ─────────────────────────────────────────────────────
    state = fields.Selection(
        selection=[
            ("draft", "Draft"),
            ("published", "Published"),
            ("archived", "Archived"),
        ],
        string="Status",
        default="draft",
        required=True,
        tracking=True,
    )
    enrollment_mode = fields.Selection(
        selection=[
            ("open", "Open"),
            ("invite", "Invite Only"),
        ],
        string="Enrollment Mode",
        default="open",
        required=True,
    )
    active = fields.Boolean(string="Active", default=True)

    # ── Relational ───────────────────────────────────────────────────────
    lesson_ids = fields.One2many(
        "education.lms.lesson",
        "course_id",
        string="Lessons",
    )
    lesson_count = fields.Integer(
        string="Lessons",
        compute="_compute_lesson_count",
        store=True,
    )
    quiz_ids = fields.One2many(
        "edu.lms.quiz",
        "course_id",
        string="Quizzes",
    )
    enrollment_ids = fields.One2many(
        "edu.lms.enrollment",
        "course_id",
        string="Enrollments",
    )
    enrollment_count = fields.Integer(
        string="Enrollments",
        compute="_compute_enrollment_count",
        store=True,
    )

    # ── Computed ─────────────────────────────────────────────────────────
    @api.depends("lesson_ids")
    def _compute_lesson_count(self):
        for rec in self:
            rec.lesson_count = len(rec.lesson_ids)

    @api.depends("enrollment_ids")
    def _compute_enrollment_count(self):
        for rec in self:
            rec.enrollment_count = len(rec.enrollment_ids)

    # ── Actions ──────────────────────────────────────────────────────────
    def action_publish(self):
        for rec in self:
            rec.state = "published"

    def action_archive_course(self):
        for rec in self:
            rec.state = "archived"

    def action_reset_draft(self):
        for rec in self:
            rec.state = "draft"
