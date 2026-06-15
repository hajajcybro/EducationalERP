# -*- coding: utf-8 -*-
"""
edu.exam.reevaluation.wizard — Re-evaluation request (S4-T06)
==============================================================
Student/admin requests a re-check of marks for a specific result.
Wizard logs the request in result history and optionally opens the result
for re-entry.
"""
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class EduExamReevaluationWizard(models.TransientModel):
    _name = "edu.exam.reevaluation.wizard"
    _description = "Re-evaluation Request"

    result_id = fields.Many2one(
        "edu.exam.result",
        string="Result",
        required=True,
        readonly=True,
    )
    student_name = fields.Char(
        related="result_id.student_name",
        readonly=True,
    )
    subject = fields.Char(
        related="result_id.subject",
        readonly=True,
    )
    current_marks = fields.Float(
        related="result_id.marks_obtained",
        readonly=True,
        string="Current Marks",
    )
    reason = fields.Text(
        string="Reason for Re-evaluation",
        required=True,
    )

    @api.constrains("reason")
    def _check_reason(self):
        for rec in self:
            if rec.reason and len(rec.reason.strip()) < 10:
                raise ValidationError(
                    _("Please provide a meaningful reason (at least 10 characters).")
                )

    def action_submit(self):
        """Log re-evaluation request and reset result to draft for re-entry."""
        self.ensure_one()
        result = self.result_id

        self.env["edu.exam.result.history"].create({
            "result_id": result.id,
            "old_marks": result.marks_obtained,
            "new_marks": result.marks_obtained,
            "changed_by_id": self.env.uid,
            "change_date": fields.Datetime.now(),
            "reason": _("[RE-EVALUATION REQUEST] %s") % self.reason,
        })

        # Reset to draft so marks can be updated
        result.write({"state": "draft"})
        result.exam_id.message_post(
            body=_(
                "Re-evaluation requested for %s — %s. Reason: %s"
            ) % (result.student_name, result.subject, self.reason)
        )

        return {
            "type": "ir.actions.act_window",
            "name": _("Result"),
            "res_model": "edu.exam.result",
            "res_id": result.id,
            "view_mode": "form",
            "target": "current",
        }
