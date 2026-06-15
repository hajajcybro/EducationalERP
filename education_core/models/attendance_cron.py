# -*- coding: utf-8 -*-
"""
education_core — Attendance Threshold Cron (S3-T05)
====================================================
Daily scheduled job that checks each enrolled student's attendance %.
If below 75%, posts a chatter message on the enrollment and
(optionally) sends a parent notification email.
"""
from odoo import models, fields, api, _


class EducationEnrollmentAttendance(models.Model):
    """Extends education.enrollment with attendance statistics."""

    _inherit = "education.enrollment"

    attendance_pct = fields.Float(
        string="Attendance %",
        compute="_compute_attendance_pct",
        store=False,
        help="% of periods marked Present or Late vs total recorded periods.",
    )
    attendance_warning = fields.Boolean(
        string="Below 75%",
        compute="_compute_attendance_pct",
        store=False,
    )

    def _compute_attendance_pct(self):
        Att = self.env["education.attendance"]
        for rec in self:
            total = Att.search_count([
                ("enrollment_id", "=", rec.id),
                ("state", "not in", ("holiday",)),
            ])
            if not total:
                rec.attendance_pct = 100.0
                rec.attendance_warning = False
                continue
            present = Att.search_count([
                ("enrollment_id", "=", rec.id),
                ("state", "in", ("present", "late", "excused")),
            ])
            pct = present / total * 100
            rec.attendance_pct = round(pct, 1)
            rec.attendance_warning = pct < 75.0

    @api.model
    def _cron_attendance_threshold_check(self):
        """
        Cron entry point — runs daily.
        Finds all active enrollments below 75% attendance and sends alerts.
        """
        active_enrollments = self.search([("state", "=", "active")])
        template = self.env.ref(
            "education_core.mail_template_attendance_warning",
            raise_if_not_found=False,
        )
        for enr in active_enrollments:
            enr._compute_attendance_pct()
            if enr.attendance_warning:
                # Post to enrollment chatter
                enr.message_post(
                    body=_(
                        "⚠ Attendance Alert: %(name)s attendance is %(pct).1f%% "
                        "(below the 75%% threshold)."
                    ) % {"name": enr.student_name, "pct": enr.attendance_pct},
                    message_type="comment",
                )
                # Email guardian
                if template and enr.guardian_email:
                    template.send_mail(enr.id, force_send=False)
