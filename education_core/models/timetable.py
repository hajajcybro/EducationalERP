# -*- coding: utf-8 -*-
"""
education.timetable — Timetable header model.
Full timetable slot lines are implemented in Sprint 3 (Attendance & Faculty).
This Sprint 1 skeleton establishes the model structure and sequence.
"""
from odoo import models, fields, api, _


WEEKDAY_SELECTION = [
    ("0", "Monday"),
    ("1", "Tuesday"),
    ("2", "Wednesday"),
    ("3", "Thursday"),
    ("4", "Friday"),
    ("5", "Saturday"),
    ("6", "Sunday"),
]


class EducationTimetable(models.Model):
    """
    Timetable header — one per class per academic year.
    Timetable slots (period × weekday grid) are added in Sprint 3.
    """

    _name = "education.timetable"
    _description = "Class Timetable"
    _order = "academic_year_id desc, class_id"
    _inherit = ["mail.thread"]

    name = fields.Char(
        string="Timetable Reference",
        compute="_compute_name",
        store=True,
    )
    class_id = fields.Many2one(
        "education.class",
        string="Class",
        required=True,
        ondelete="cascade",
        tracking=True,
        index=True,
    )
    academic_year_id = fields.Many2one(
        "education.academic.year",
        string="Academic Year",
        required=True,
        ondelete="restrict",
        tracking=True,
        index=True,
    )
    effective_from = fields.Date(
        string="Effective From",
        help="Date from which this timetable is active.",
    )
    effective_to = fields.Date(
        string="Effective To",
        help="Leave blank if there is no fixed end date.",
    )

    # ── Timetable Slots (Sprint 3) ─────────────────────────────────────────
    slot_ids = fields.One2many(
        "education.timetable.slot",
        "timetable_id",
        string="Timetable Slots",
    )
    slot_count = fields.Integer(
        string="# Slots",
        compute="_compute_slot_count",
    )

    state = fields.Selection(
        selection=[
            ("draft", "Draft"),
            ("published", "Published"),
            ("archived", "Archived"),
        ],
        string="Status",
        default="draft",
        tracking=True,
    )
    notes = fields.Text(string="Notes")
    active = fields.Boolean(default=True)

    _class_year_uniq =models.Constraint(
            "UNIQUE(class_id, academic_year_id)",
            "A timetable for this class and academic year already exists.",
        )


    @api.depends("slot_ids")
    def _compute_slot_count(self):
        for rec in self:
            rec.slot_count = len(rec.slot_ids)

    @api.depends("class_id", "academic_year_id")
    def _compute_name(self):
        for rec in self:
            rec.name = (
                f"TT/{rec.class_id.name or ''}"
                f"/{rec.academic_year_id.code or ''}"
            )

    def action_publish(self):
        self.write({"state": "published"})

    def action_reset_draft(self):
        self.write({"state": "draft"})

