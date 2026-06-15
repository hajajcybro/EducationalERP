# -*- coding: utf-8 -*-
"""
edu.exam.mark.entry.wizard — Bulk mark entry (S4-T09)
=======================================================
Select exam + subject → table of all enrolled students loads.
Teacher enters marks per student and saves in bulk.
"""
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class EduExamMarkEntryWizard(models.TransientModel):
    _name = "edu.exam.mark.entry.wizard"
    _description = "Bulk Mark Entry Wizard"

    exam_id = fields.Many2one(
        "edu.exam",
        string="Exam",
        required=True,
        domain="[('state', 'in', ['scheduled', 'ongoing'])]",
    )
    subject = fields.Char(
        string="Subject",
        required=True,
    )
    class_id = fields.Many2one(
        "education.class",
        string="Class",
        required=True,
    )
    max_marks = fields.Float(
        string="Max Marks",
        required=True,
        default=100.0,
    )
    pass_marks = fields.Float(
        string="Pass Marks",
        required=True,
        default=40.0,
    )
    line_ids = fields.One2many(
        "edu.exam.mark.entry.line",
        "wizard_id",
        string="Student Marks",
    )

    @api.onchange("exam_id", "subject", "class_id")
    def _onchange_load_students(self):
        if not (self.exam_id and self.class_id):
            return
        enrollments = self.env["education.enrollment"].search([
            ("class_id", "=", self.class_id.id),
            ("state", "=", "active"),
        ], order="student_name")

        # Get subject defaults from exam subject lines
        subj_line = self.exam_id.subject_line_ids.filtered(
            lambda l: l.subject == self.subject
        )[:1]
        if subj_line:
            self.max_marks = subj_line.max_marks
            self.pass_marks = subj_line.pass_marks

        lines = []
        for enr in enrollments:
            existing = self.env["edu.exam.result"].search([
                ("exam_id", "=", self.exam_id.id),
                ("enrollment_id", "=", enr.id),
                ("subject", "=", self.subject),
            ], limit=1)
            lines.append((0, 0, {
                "enrollment_id": enr.id,
                "marks_obtained": existing.marks_obtained if existing else 0.0,
                "absent": existing.absent if existing else False,
            }))
        self.line_ids = lines

    @api.constrains("pass_marks", "max_marks")
    def _check_marks(self):
        for rec in self:
            if rec.pass_marks > rec.max_marks:
                raise ValidationError(
                    _("Pass marks cannot exceed max marks.")
                )

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
                ("subject", "=", self.subject),
            ], limit=1)
            vals = {
                "marks_obtained": line.marks_obtained,
                "absent": line.absent,
                "max_marks": self.max_marks,
                "pass_marks": self.pass_marks,
            }
            if existing:
                existing.write(vals)
            else:
                Result.create({
                    "exam_id": self.exam_id.id,
                    "enrollment_id": line.enrollment_id.id,
                    "subject": self.subject,
                    **vals,
                })
            saved += 1

        self.exam_id.message_post(
            body=_(
                "Marks saved for %d students — %s / %s."
            ) % (saved, self.subject, self.class_id.name)
        )
        return {
            "type": "ir.actions.act_window",
            "name": _("Results — %s") % self.subject,
            "res_model": "edu.exam.result",
            "view_mode": "list,form",
            "domain": [
                ("exam_id", "=", self.exam_id.id),
                ("subject", "=", self.subject),
                ("class_id", "=", self.class_id.id),
            ],
        }


class EduExamMarkEntryLine(models.TransientModel):
    _name = "edu.exam.mark.entry.line"
    _description = "Mark Entry Line"
    _order = "student_name"

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
    marks_obtained = fields.Float(
        string="Marks",
        default=0.0,
    )
    absent = fields.Boolean(
        string="Absent",
        default=False,
    )
