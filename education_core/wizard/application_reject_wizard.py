# -*- coding: utf-8 -*-
"""
education.application.reject.wizard
====================================
Captures rejection reason and transitions the application to 'rejected'.
Triggers the rejection email template.
"""
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class ApplicationRejectWizard(models.TransientModel):
    _name = "education.application.reject.wizard"
    _description = "Application Rejection Wizard"

    application_id = fields.Many2one(
        "education.application",
        string="Application",
        required=True,
        readonly=True,
    )
    applicant_name = fields.Char(
        string="Applicant",
        related="application_id.name",
        readonly=True,
    )
    program_name = fields.Char(
        string="Program",
        related="application_id.program_id.name",
        readonly=True,
    )
    rejection_reason = fields.Text(
        string="Rejection Reason",
        required=True,
        help="This reason will be included in the rejection email sent to the applicant.",
    )

    @api.constrains("rejection_reason")
    def _check_reason(self):
        for rec in self:
            if rec.rejection_reason and len(rec.rejection_reason.strip()) < 10:
                raise ValidationError(
                    _("Please provide a meaningful rejection reason (at least 10 characters).")
                )

    def action_confirm_reject(self):
        self.ensure_one()
        self.application_id.write({
            "state": "rejected",
            "rejection_reason": self.rejection_reason,
            "rejected_by_id": self.env.uid,
            "rejection_date": fields.Date.today(),
        })
        # Send rejection email
        template = self.env.ref(
            "education_core.mail_template_application_rejected",
            raise_if_not_found=False,
        )
        if template:
            template.send_mail(self.application_id.id, force_send=False)
        # Post to chatter
        self.application_id.message_post(
            body=_("Application rejected. Reason: %s") % self.rejection_reason,
        )
        return {"type": "ir.actions.act_window_close"}
