# -*- coding: utf-8 -*-
"""
LMS Lesson model (S7-T02)
==========================
education.lms.lesson — individual learning unit inside a course.
"""
from odoo import models, fields


class EducationLmsLesson(models.Model):
    """A single lesson (video, PDF, slide or URL) belonging to a course."""

    _name = "education.lms.lesson"
    _description = "LMS Lesson"
    _order = "course_id, sequence"
    _rec_name = "title"

    course_id = fields.Many2one(
        "education.lms.course",
        string="Course",
        required=True,
        ondelete="cascade",
        index=True,
    )
    title = fields.Char(string="Lesson Title", required=True)
    lesson_type = fields.Selection(
        selection=[
            ("video", "Video"),
            ("pdf", "PDF"),
            ("slide", "Slide"),
            ("url", "URL"),
        ],
        string="Type",
        default="video",
        required=True,
    )
    content_url = fields.Char(string="Content URL")
    sequence = fields.Integer(string="Sequence", default=10)
    duration_mins = fields.Integer(string="Duration (mins)", default=0)
    active = fields.Boolean(string="Active", default=True)
