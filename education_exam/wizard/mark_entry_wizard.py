# -*- coding: utf-8 -*-
"""
edu.exam.mark.entry.wizard — Bulk mark entry (S4-T09)
=======================================================
Select Exam + Class → every enrolled student × every subject scheduled
for that exam loads automatically. Teacher enters marks and saves in bulk.
"""
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class EduExamMarkEntryWizard(models.TransientModel):
    _name = "edu.exam.mark.entry.wizard"
    _description = "Bulk Mark Entry Wizard"

    exam_id = fields.Many2one(
        "edu.exam",
        string="Exam",
        required=True,
        domain="[('state', 'in', ['scheduled', 'ongoing'])]",
    )
    class_id = fields.Many2one(
        "education.class",
        string="Class",
        required=True,
    )
    line_ids = fields.One2many(
        "edu.exam.mark.entry.line",
        "wizard_id",
        string="Student Marks",
    )

    @api.onchange("exam_id", "class_id")
    def _onchange_load(self):
        """Load all students × all exam subjects when both fields are set."""
        self.line_ids = [(5, 0, 0)]
        if not (self.exam_id and self.class_id):
            return

        enrollments = self.env["education.enrollment"].search([
            ("class_id", "=", self.class_id.id),
            ("state", "=", "active"),
        ], order="student_name")

        subject_lines = self.exam_id.subject_line_ids
        if not enrollments or not subject_lines:
            return

        lines = []
        for enr in enrollments:
            for subj_line in subject_lines:
                existing = self.env["edu.exam.result"].search([
                    ("exam_id", "=", self.exam_id.id),
                    ("enrollment_id", "=", enr.id),
                    ("subject_id", "=", subj_line.subject_id.id),
                ], limit=1)
                lines.append((0, 0, {
                    "enrollment_id": enr.id,
                    "subject_id": subj_line.subject_id.id,
                    "max_marks": subj_line.max_marks,
                    "pass_marks": subj_line.pass_marks,
                    "marks_obtained": existing.marks_obtained if existing else 0.0,
                    "absent": existing.absent if existing else False,
                }))
        self.line_ids = lines

    def action_save_marks(self):
        """Create or update edu.exam.result for each line."""
        self.ensure_one()
        if not self.line_ids:
            raise UserError(_("No student lines to save."))

        Result = self.env["edu.exam.result"]
        saved = 0
        for line in self.line_ids:
            existing = Result.search([
                ("exam_id", "=", self.exam_id.id),
                ("enrollment_id", "=", line.enrollment_id.id),
                ("subject_id", "=", line.subject_id.id),
            ], limit=1)
            vals = {
                "marks_obtained": line.marks_obtained,
                "absent": line.absent,
                "max_marks": line.max_marks,
                "pass_marks": line.pass_marks,
            }
            if existing:
                existing.write(vals)
            else:
                Result.create({
                    "exam_id": self.exam_id.id,
                    "enrollment_id": line.enrollment_id.id,
                    "subject_id": line.subject_id.id,
                    **vals,
                })
            saved += 1

        self.exam_id.message_post(
            body=_("Marks saved for %d entries — %s.") % (saved, self.class_id.name)
        )
        return {
            "type": "ir.actions.act_window",
            "name": _("Results — %s") % self.class_id.name,
            "res_model": "edu.exam.result",
            "view_mode": "list,form",
            "domain": [
                ("exam_id", "=", self.exam_id.id),
                ("class_id", "=", self.class_id.id),
            ],
        }


class EduExamMarkEntryLine(models.TransientModel):
    _name = "edu.exam.mark.entry.line"
    _description = "Mark Entry Line"
    _order = "student_name, subject_id"

    wizard_id = fields.Many2one(
        "edu.exam.mark.entry.wizard",
        ondelete="cascade",
        required=True,
    )
    enrollment_id = fields.Many2one(
        "education.enrollment",
        string="Student",
        required=True,
        readonly=True,
    )
    student_name = fields.Char(
        related="enrollment_id.student_name",
        store=True,
        readonly=True,
    )
    subject_id = fields.Many2one(
        "education.subject",
        string="Subject",
        required=True,
        readonly=True,
    )
    max_marks = fields.Float(string="Max", default=100.0, readonly=True)
    pass_marks = fields.Float(string="Pass", default=40.0, readonly=True)
    marks_obtained = fields.Float(string="Marks", default=0.0)
    absent = fields.Boolean(string="Absent", default=False)
