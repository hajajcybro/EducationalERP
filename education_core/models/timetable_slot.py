# -*- coding: utf-8 -*-
"""
education.timetable.slot — Individual period entries within a timetable (S3-T02)
=================================================================================
One slot = one period on one weekday for a class timetable.
Linked to education.timetable (header) via Many2one.
"""
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class EducationTimetableSlot(models.Model):
    """A single period slot in a class timetable."""

    _name = "education.timetable.slot"
    _description = "Timetable Slot"
    _order = "weekday, period_no"

    timetable_id = fields.Many2one(
        "education.timetable",
        string="Timetable",
        required=True,
        ondelete="cascade",
        index=True,
    )
    class_id = fields.Many2one(
        "education.class",
        string="Class",
        related="timetable_id.class_id",
        store=True,
        readonly=True,
    )
    academic_year_id = fields.Many2one(
        "education.academic.year",
        related="timetable_id.academic_year_id",
        store=True,
        readonly=True,
    )

    # ── Slot Details ──────────────────────────────────────────────────────
    weekday = fields.Selection(
        selection=[
            ("0", "Monday"),
            ("1", "Tuesday"),
            ("2", "Wednesday"),
            ("3", "Thursday"),
            ("4", "Friday"),
            ("5", "Saturday"),
            ("6", "Sunday"),
        ],
        string="Day",
        required=True,
    )
    period_no = fields.Integer(
        string="Period",
        required=True,
        default=1,
        help="Period number within the day (1 = first period).",
    )
    start_time = fields.Float(
        string="Start Time",
        help="24-hour format, e.g. 9.5 = 09:30.",
    )
    end_time = fields.Float(
        string="End Time",
    )
    subject = fields.Char(
        string="Subject",
        help="Subject / Course taught in this slot. "
             "Will be linked to course catalog in Sprint 4.",
    )
    teacher_id = fields.Many2one(
        "education.faculty",
        string="Teacher",
        ondelete="set null",
        help="Assigned faculty member for this slot.",
    )
    room = fields.Char(string="Room / Lab")
    notes = fields.Char(string="Notes")

    _slot_unique = models.Constraint(
            "UNIQUE(timetable_id, weekday, period_no)",
            "A slot for this day and period already exists in this timetable.",
        )


    @api.constrains("start_time", "end_time")
    def _check_times(self):
        for rec in self:
            if rec.start_time and rec.end_time and rec.end_time <= rec.start_time:
                raise ValidationError(
                    _("End Time must be after Start Time for slot %s P%s.")
                    % (dict(self._fields["weekday"].selection).get(rec.weekday), rec.period_no)
                )

    @api.constrains("period_no")
    def _check_period_no(self):
        for rec in self:
            if rec.period_no < 1:
                raise ValidationError(_("Period number must be at least 1."))

    def name_get(self):
        """Legacy compatibility — Odoo 19 uses display_name, but kept for safety."""
        result = []
        weekday_labels = dict(self._fields["weekday"].selection)
        for rec in self:
            label = f"{weekday_labels.get(rec.weekday, '?')} P{rec.period_no}"
            if rec.subject:
                label += f" — {rec.subject}"
            result.append((rec.id, label))
        return result
