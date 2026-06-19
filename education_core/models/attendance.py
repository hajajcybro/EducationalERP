# -*- coding: utf-8 -*-
"""
education.attendance — Per-student per-period attendance record (S3-T01)
=========================================================================
One record per student per period per date.
Supports bulk marking (all-present) and parent SMS/email notification.
"""
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class EducationAttendance(models.Model):
    """Single attendance record: one student, one period, one date."""

    _name = "education.attendance"
    _description = "Student Attendance"
    _inherit = ["mail.thread"]
    _order = "date desc, period_no"
    _rec_name = "display_name"

    display_name = fields.Char(
        compute="_compute_display_name",
        store=True,
    )

    # ── Relationships ─────────────────────────────────────────────────────
    enrollment_id = fields.Many2one(
        "education.enrollment",
        string="Student Enrollment",
        required=True,
        ondelete="cascade",
        index=True,
    )


    student_name = fields.Char(
        related="enrollment_id.student_name",
        store=True,
        string="Student",
        readonly=True,
    )

    class_id = fields.Many2one(
        "education.class",
        string="Class",
        related="enrollment_id.class_id",
        store=True,
        index=True,
    )
    academic_year_id = fields.Many2one(
        "education.academic.year",
        related="enrollment_id.academic_year_id",
        store=True,
    )
    timetable_slot_id = fields.Many2one(
        "education.timetable.slot",
        string="Timetable Slot",
        ondelete="set null",
        help="Link to timetable slot (optional — allows reporting by subject).",
    )

    # ── Attendance Details ────────────────────────────────────────────────
    date = fields.Date(
        string="Date",
        required=True,
        default=fields.Date.today,
        index=True,
    )
    period_no = fields.Integer(
        string="Period",
        required=True,
        default=1,
    )
    subject = fields.Char(
        string="Subject",
        related="timetable_slot_id.subject",
        store=True,
        readonly=True,
    )
    state = fields.Selection(
        selection=[
            ("present", "Present"),
            ("absent", "Absent"),
            ("late", "Late"),
            ("excused", "Excused"),
            ("holiday", "Holiday / Off"),
        ],
        string="Status",
        required=True,
        default="present",
        tracking=True,
    )
    marked_by_id = fields.Many2one(
        "res.users",
        string="Marked By",
        default=lambda self: self.env.uid,
        readonly=True,
    )
    notes = fields.Char(string="Notes / Remarks")

    # ── System ────────────────────────────────────────────────────────────
    company_id = fields.Many2one(
        "res.company",
        related="enrollment_id.company_id",
        store=True,
        readonly=True,
    )

    _enrollment_date_period_uniq = models.Constraint(
            "UNIQUE(enrollment_id, date, period_no)",
            "Attendance for this student, date and period already exists.", )


    # ── Computed ───────────────────────────────────────────────────────────

    @api.depends("student_name", "date", "period_no")
    def _compute_display_name(self):
        for rec in self:
            rec.display_name = (
                f"{rec.student_name or '?'} / "
                f"{rec.date or '?'} / P{rec.period_no}"
            )

    # ── Constraints ────────────────────────────────────────────────────────

    @api.constrains("date")
    def _check_date(self):
        today = fields.Date.today()
        for rec in self:
            if rec.date and rec.date > today:
                raise ValidationError(
                    _("Attendance date cannot be in the future.")
                )

    @api.constrains("period_no")
    def _check_period(self):
        for rec in self:
            if rec.period_no < 1:
                raise ValidationError(_("Period number must be at least 1."))

    # ── Business Methods ───────────────────────────────────────────────────

    @api.model
    def bulk_mark_present(self, class_id, date, period_no):
        """
        Mark all active enrollments in a class as Present for a given period.
        Returns count of records created.
        """
        enrollments = self.env["education.enrollment"].search([
            ("class_id", "=", class_id),
            ("state", "=", "active"),
        ])
        created = 0
        for enr in enrollments:
            existing = self.search([
                ("enrollment_id", "=", enr.id),
                ("date", "=", date),
                ("period_no", "=", period_no),
            ], limit=1)
            if not existing:
                self.create({
                    "enrollment_id": enr.id,
                    "date": date,
                    "period_no": period_no,
                    "state": "present",
                })
                created += 1
        return created

    def action_notify_parent(self):
        """Send absence notification email to guardian."""
        absent = self.filtered(lambda r: r.state == "absent")
        template = self.env.ref(
            "education_core.mail_template_attendance_absent",
            raise_if_not_found=False,
        )
        if template:
            for rec in absent:
                if rec.enrollment_id.guardian_email:
                    template.send_mail(rec.id, force_send=False)
