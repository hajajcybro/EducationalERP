# Copyright 2025 Cybrosys Techno Solutions
# License LGPL-3 - See https://www.gnu.org/licenses/lgpl-3.0.html

import logging
from datetime import datetime

from odoo import api, fields, models, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class EduNotificationQueue(models.Model):
    _name = "edu.notification.queue"
    _description = "Notification Queue"
    _order = "create_date desc"

    name = fields.Char(
        string="Name",
        compute="_compute_name",
        store=True,
    )
    notif_type = fields.Selection(
        selection=[
            ("email", "Email"),
            ("sms", "SMS"),
            ("inapp", "In-App"),
        ],
        string="Type",
        default="email",
        required=True,
    )
    recipient_id = fields.Many2one(
        comodel_name="res.partner",
        string="Recipient",
        required=True,
        ondelete="cascade",
    )
    template_id = fields.Many2one(
        comodel_name="mail.template",
        string="Mail Template",
        ondelete="set null",
    )
    subject = fields.Char(string="Subject")
    body = fields.Text(string="Body", required=True)
    state = fields.Selection(
        selection=[
            ("pending", "Pending"),
            ("sent", "Sent"),
            ("failed", "Failed"),
        ],
        string="State",
        default="pending",
        required=True,
    )
    retry_count = fields.Integer(
        string="Retry Count",
        default=0,
        readonly=True,
    )
    sent_date = fields.Datetime(string="Sent Date", readonly=True)
    error_message = fields.Text(string="Error Message", readonly=True)

    # ------------------------------------------------------------------
    # Computed
    # ------------------------------------------------------------------

    @api.depends("notif_type", "recipient_id")
    def _compute_name(self):
        type_label = dict(self._fields["notif_type"].selection)
        for rec in self:
            label = type_label.get(rec.notif_type, "")
            recipient = rec.recipient_id.name or ""
            rec.name = f"[{label}] {recipient}" if recipient else f"[{label}]"

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    def action_send(self):
        """Send the notification according to its type."""
        for rec in self:
            try:
                if rec.notif_type == "email":
                    rec._send_email()
                elif rec.notif_type == "sms":
                    rec._send_sms()
                elif rec.notif_type == "inapp":
                    rec._send_inapp()
                rec.write({
                    "state": "sent",
                    "sent_date": fields.Datetime.now(),
                    "error_message": False,
                })
            except Exception as exc:
                _logger.exception(
                    "education_notification: failed to send notification %s", rec.id
                )
                rec.write({
                    "state": "failed",
                    "error_message": str(exc),
                })

    def action_retry(self):
        """Reset to pending and attempt re-send."""
        self.write({
            "state": "pending",
            "error_message": False,
        })
        self.write({"retry_count": self.retry_count + 1})
        self.action_send()

    def action_mark_failed(self):
        """Force state to failed without sending."""
        self.write({"state": "failed"})

    # ------------------------------------------------------------------
    # Private send helpers
    # ------------------------------------------------------------------

    def _send_email(self):
        """Create and send a mail.mail record."""
        self.ensure_one()
        MailMail = self.env["mail.mail"]
        mail_values = {
            "subject": self.subject or _("Notification"),
            "body_html": self.body,
            "email_to": self.recipient_id.email,
            "auto_delete": True,
        }
        if self.recipient_id.email:
            mail = MailMail.create(mail_values)
            mail.send()
        else:
            raise UserError(
                _("Recipient %s has no email address.", self.recipient_id.name)
            )

    def _send_sms(self):
        """SMS stub — logs a message; wire up a real SMS provider here."""
        self.ensure_one()
        _logger.info(
            "education_notification: SMS stub — would send to %s: %s",
            self.recipient_id.name,
            self.body,
        )

    def _send_inapp(self):
        """Create an edu.notification.centre record for the recipient's user."""
        self.ensure_one()
        user = self.env["res.users"].search(
            [("partner_id", "=", self.recipient_id.id)], limit=1
        )
        if user:
            self.env["edu.notification.centre"].create({
                "user_id": user.id,
                "title": self.subject or _("Notification"),
                "message": self.body,
            })
        else:
            _logger.warning(
                "education_notification: no user found for partner %s (%s)",
                self.recipient_id.name,
                self.recipient_id.id,
            )

    # ------------------------------------------------------------------
    # Cron
    # ------------------------------------------------------------------

    @api.model
    def _cron_process_queue(self):
        """Process all pending notifications (called by scheduled action)."""
        pending = self.search([("state", "=", "pending")])
        _logger.info(
            "education_notification: cron processing %d pending notification(s)",
            len(pending),
        )
        pending.action_send()


class EduNotificationCentre(models.Model):
    _name = "edu.notification.centre"
    _description = "In-App Notification"
    _order = "create_date desc"

    user_id = fields.Many2one(
        comodel_name="res.users",
        string="User",
        required=True,
        default=lambda self: self.env.uid,
        ondelete="cascade",
    )
    title = fields.Char(string="Title", required=True)
    message = fields.Text(string="Message")
    is_read = fields.Boolean(string="Read", default=False)
    notification_date = fields.Datetime(
        string="Date",
        default=fields.Datetime.now,
    )
    link_model = fields.Char(
        string="Related Model",
        help="Optional model name for navigation (e.g. 'edu.student').",
    )
    link_res_id = fields.Integer(
        string="Related Record ID",
        help="Optional record ID in the related model.",
    )

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    def action_mark_read(self):
        """Mark the selected notification(s) as read."""
        self.write({"is_read": True})
