# -*- coding: utf-8 -*-
"""
LMS Quiz engine models (S7-T03)
================================
edu.lms.quiz          — quiz header linked to a course
edu.lms.quiz.question — individual question (MCQ / True-False / Fill-blank)
edu.lms.quiz.option   — answer option for MCQ questions
"""
from odoo import models, fields, api


class EduLmsQuiz(models.Model):
    """Quiz — set of questions attached to an LMS course."""

    _name = "edu.lms.quiz"
    _description = "LMS Quiz"
    _order = "course_id, title"
    _rec_name = "title"

    course_id = fields.Many2one(
        "education.lms.course",
        string="Course",
        required=True,
        ondelete="cascade",
        index=True,
    )
    title = fields.Char(string="Quiz Title", required=True)
    pass_marks = fields.Float(string="Pass Marks (%)", default=50.0)
    time_limit_mins = fields.Integer(string="Time Limit (mins)", default=30)
    max_attempts = fields.Integer(string="Max Attempts", default=3)

    question_ids = fields.One2many(
        "edu.lms.quiz.question",
        "quiz_id",
        string="Questions",
    )
    question_count = fields.Integer(
        string="Questions",
        compute="_compute_question_count",
        store=True,
    )

    @api.depends("question_ids")
    def _compute_question_count(self):
        for rec in self:
            rec.question_count = len(rec.question_ids)


class EduLmsQuizQuestion(models.Model):
    """A single question inside a quiz."""

    _name = "edu.lms.quiz.question"
    _description = "LMS Quiz Question"
    _order = "quiz_id, sequence"
    _rec_name = "question_text"

    quiz_id = fields.Many2one(
        "edu.lms.quiz",
        string="Quiz",
        required=True,
        ondelete="cascade",
        index=True,
    )
    sequence = fields.Integer(string="Sequence", default=10)
    question_text = fields.Char(string="Question", required=True)
    question_type = fields.Selection(
        selection=[
            ("mcq", "MCQ"),
            ("true_false", "True/False"),
            ("fill_blank", "Fill in Blank"),
        ],
        string="Question Type",
        default="mcq",
        required=True,
    )
    correct_answer = fields.Char(
        string="Correct Answer",
        help=(
            "For true/false: 'true' or 'false'. "
            "For fill_blank: expected answer. "
            "For MCQ: leave blank, mark the correct option instead."
        ),
    )
    marks = fields.Float(string="Marks", default=1.0)

    option_ids = fields.One2many(
        "edu.lms.quiz.option",
        "question_id",
        string="Options",
    )


class EduLmsQuizOption(models.Model):
    """An answer option for an MCQ question."""

    _name = "edu.lms.quiz.option"
    _description = "LMS Quiz Option"
    _order = "question_id, id"
    _rec_name = "option_text"

    question_id = fields.Many2one(
        "edu.lms.quiz.question",
        string="Question",
        required=True,
        ondelete="cascade",
        index=True,
    )
    option_text = fields.Char(string="Option", required=True)
    is_correct = fields.Boolean(string="Correct Answer", default=False)
