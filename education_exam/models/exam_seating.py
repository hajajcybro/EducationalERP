# -*- coding: utf-8 -*-
"""
edu.exam.seating — Hall seating plan (S4-T02)
edu.exam.invigilator — Invigilator assignment (S4-T03)
=======================================================
One seating record per student per exam.
One invigilator record per faculty per hall per date.
"""
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class EduExamSeating(models.Model):
    """Seating assignment — student → exam hall + seat number."""

    _name = "edu.exam.seating"
    _description = "Exam Seating Assignment"
    _order = "classroom_id, seat_no"
    _rec_name = "roll_no"

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
        string="Student Name",
    )
    class_id = fields.Many2one(
        "education.class",
        related="enrollment_id.class_id",
        store=True,
        readonly=True,
    )
    roll_no = fields.Char(
        string="Roll No.",
        required=True,
    )
    classroom_id = fields.Many2one(
        "edu.classroom",
        string="Exam Hall",
    )
    seat_no = fields.Char(string="Seat No.")

    _sql_constraints = [
        (
            "exam_enrollment_uniq",
            "UNIQUE(exam_id, enrollment_id)",
            "This student already has a seating assignment for this exam.",
        ),
        (
            "exam_roll_uniq",
            "UNIQUE(exam_id, roll_no)",
            "Roll number must be unique within the exam.",
        ),
    ]


class EduExamInvigilator(models.Model):
    """Invigilator assignment — faculty supervises a hall on an exam date."""

    _name = "edu.exam.invigilator"
    _description = "Exam Invigilator"
    _order = "date, classroom_id"

    exam_id = fields.Many2one(
        "edu.exam",
        string="Exam",
        required=True,
        ondelete="cascade",
        index=True,
    )
    faculty_id = fields.Many2one(
        "education.faculty",
        string="Faculty",
        required=True,
    )
    faculty_name = fields.Char(
        related="faculty_id.name",
        store=True,
        readonly=True,
    )
    classroom_id = fields.Many2one(
        "edu.classroom",
        string="Exam Hall",
        required=True,
    )
    date = fields.Date(
        string="Date",
        required=True,
    )
    subject = fields.Char(
        string="Subject / Session",
        help="Which paper / session this invigilator is assigned to.",
    )
    notes = fields.Char(string="Notes")

    @api.constrains("date", "exam_id")
    def _check_date_in_range(self):
        for rec in self:
            exam = rec.exam_id
            if exam.date_from and exam.date_to:
                if not (exam.date_from <= rec.date <= exam.date_to):
                    raise ValidationError(
                        _(
                            "Invigilator date %s is outside exam period %s – %s."
                        ) % (rec.date, exam.date_from, exam.date_to)
                    )
