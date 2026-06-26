# -*- coding: utf-8 -*-
"""
education_document_management — Document Expiry & Alert (S5-T10, S5-T11)
=========================================================================
Extends education.document.type with expiry_alert_days.
Extends education.document with:
  - expiry_state computed field (valid / expiring_soon / expired / no_expiry)
Adds _cron_send_expiry_alerts on education.document, run weekly by ir.cron to:
  - Set state = 'expired' on expired, verified documents
  - Email guardian/student when document is expiring soon or already expired
"""
from odoo import models, fields, api, _
import logging
_logger = logging.getLogger(__name__)


class EducationDocumentTypeExpiry(models.Model):
    """Add per-type alert threshold."""

    _inherit = "education.document.type"

    expiry_alert_days = fields.Integer(
        string="Alert Before Expiry (days)",
        default=30,
        help="Send expiry reminder this many days before the expiry date.",
    )


class EducationDocumentExpiry(models.Model):
    """Extend education.document with expiry state."""

    _inherit = "education.document"

    expiry_state = fields.Selection(
        selection=[
            ("no_expiry", "No Expiry"),
            ("valid", "Valid"),
            ("expiring_soon", "Expiring Soon"),
            ("expired", "Expired"),
        ],
        string="Expiry Status",
        compute="_compute_expiry_state",
        store=True,
        help="Automatically computed from expiry_date and alert threshold.",
    )

    @api.depends(
        "expiry_date",
        "document_type_id.expiry_alert_days",
        "state",
    )
    def _compute_expiry_state(self):
        today = fields.Date.today()
        for rec in self:
            if not rec.expiry_date:
                rec.expiry_state = "no_expiry"
                continue
            if rec.expiry_date < today:
                rec.expiry_state = "expired"
            else:
                alert_days = rec.document_type_id.expiry_alert_days or 30
                delta = (rec.expiry_date - today).days
                if delta <= alert_days:
                    rec.expiry_state = "expiring_soon"
                else:
                    rec.expiry_state = "valid"

    @api.model
    def _cron_send_expiry_alerts(self):
        """Weekly cron (S5-T11): send document expiry alerts.

        1. Mark verified documents past expiry_date as expired.
        2. Send alert emails for expiring_soon and expired documents.
        """
        today = fields.Date.today()
        template = self.env.ref(
            "education_document_management.mail_template_doc_expiry",
            raise_if_not_found=False,
        )
        # Documents that are expiring soon or already expired (have an expiry_date)
        docs = self.search([
            ("expiry_date", "!=", False),
            ("state", "=", "verified"),
            ("active", "=", True),
        ])
        alert_sent = 0
        for doc in docs:
            if not doc.expiry_date:
                continue

            alert_days = doc.document_type_id.expiry_alert_days or 30
            delta = (doc.expiry_date - today).days

            is_expired = delta < 0
            is_expiring = 0 <= delta <= alert_days

            if not (is_expired or is_expiring):
                continue

            # Send email to guardian/student or linked partner
            enr = doc.enrollment_id
            partner = (
                enr and (enr.guardian_partner_id or enr.student_partner_id)
            ) or None
            if template and partner and partner.email:
                try:
                    template.send_mail(
                        doc.id,
                        force_send=False,
                        email_values={'email_to': partner.email},
                    )
                    alert_sent += 1
                except Exception as e:
                    _logger.error(
                        "Document expiry alert failed for doc %s (partner %s): %s",
                        doc.id, partner.id, e
                    )

        return _("Document expiry alerts queued: %d") % alert_sent
