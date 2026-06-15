# -*- coding: utf-8 -*-
"""
education.attendance.summary.wizard — S3-T07
============================================
Filters attendance by class + date range and either opens the list view
or triggers the PDF attendance report.
"""
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class AttendanceSummaryWizard(models.TransientModel):
    _name = "education.attendance.summary.wizard"
    _description = "Attendance Summary Wizard"

    class_id = fields.Many2one(
        "education.class",
        string="Class",
        required=True,
    )
    date_from = fields.Date(
        string="From Date",
        required=True,
        default=lambda self: fields.Date.today().replace(day=1),
    )
    date_to = fields.Date(
        string="To Date",
        required=True,
        default=fields.Date.today,
    )

    @api.constrains("date_from", "date_to")
    def _check_dates(self):
        for rec in self:
            if rec.date_from and rec.date_to and rec.date_to < rec.date_from:
                raise ValidationError(_("To Date must be on or after From Date."))

    def _get_domain(self):
        return [
            ("class_id", "=", self.class_id.id),
            ("date", ">=", self.date_from),
            ("date", "<=", self.date_to),
        ]

    def action_view_attendance(self):
        """Open the attendance list filtered by wizard parameters."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Attendance — %s") % self.class_id.name,
            "res_model": "education.attendance",
            "view_mode": "list,form",
            "domain": self._get_domain(),
            "context": {
                "default_class_id": self.class_id.id,
                "search_default_date_range": 1,
            },
        }

    def action_print_report(self):
        """Render the QWeb PDF attendance report."""
        self.ensure_one()
        records = self.env["education.attendance"].search(self._get_domain())
        if not records:
            raise ValidationError(
                _("No attendance records found for the selected class and date range.")
            )
        return self.env.ref(
            "education_core.action_report_attendance_period"
        ).report_action(
            records,
            data={
                "class_name": self.class_id.name,
                "date_from": str(self.date_from),
                "date_to": str(self.date_to),
            },
        )
