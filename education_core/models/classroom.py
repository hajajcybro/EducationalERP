# -*- coding: utf-8 -*-
"""
edu.classroom — Physical room/hall management (S4-T12)
=======================================================
Rooms used for teaching and examinations. Referenced by timetable slots
and exam seating plans.
"""
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class EduClassroom(models.Model):
    """Physical classroom, lab, or exam hall."""

    _name = "edu.classroom"
    _description = "Classroom / Exam Hall"
    _order = "block, room_no"
    _rec_name = "display_name"

    display_name = fields.Char(
        compute="_compute_display_name",
        store=True,
    )
    room_no = fields.Char(
        string="Room No.",
        required=True,
    )
    block = fields.Char(
        string="Block / Building",
        help="e.g. A, B, Science Block",
    )
    capacity = fields.Integer(
        string="Capacity (seats)",
        default=30,
    )
    room_type = fields.Selection(
        selection=[
            ("classroom", "Classroom"),
            ("lab", "Laboratory"),
            ("hall", "Exam Hall"),
            ("auditorium", "Auditorium"),
            ("seminar", "Seminar Room"),
        ],
        string="Type",
        required=True,
        default="classroom",
    )
    floor = fields.Char(string="Floor")
    active = fields.Boolean(default=True)
    notes = fields.Text(string="Notes")

    _sql_constraints = [
        (
            "room_no_block_uniq",
            "UNIQUE(room_no, block)",
            "A room with this number already exists in the same block.",
        )
    ]

    @api.depends("room_no", "block")
    def _compute_display_name(self):
        for rec in self:
            rec.display_name = (
                f"{rec.block}-{rec.room_no}" if rec.block else rec.room_no or "?"
            )

    @api.constrains("capacity")
    def _check_capacity(self):
        for rec in self:
            if rec.capacity < 1:
                raise ValidationError(_("Capacity must be at least 1."))
