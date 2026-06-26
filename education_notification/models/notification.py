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
    _rec_name = 'name'



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
        """Send a real SMS via Odoo's community ``sms`` module.

        Creates an ``sms.sms`` record and dispatches it through the configured
        SMS gateway. Per-message failures (missing number, no credit, …) set the
        record's state to ``error``; we surface those as a ``UserError`` so the
        notification is marked ``failed`` with a meaningful message.
        """
        self.ensure_one()
        number = self.recipient_id.phone
        if not number:
            raise UserError(
                _("Recipient %s has no phone number.", self.recipient_id.name)
            )
        sms = self.env["sms.sms"].create({
            "number": number,
            "body": self.body,
            "partner_id": self.recipient_id.id,
        })
        # Keep the sms.sms record for traceability (unlink_sent=False) and let
        # gateway/connection errors propagate (raise_exception=True).
        sms.send(unlink_failed=False, unlink_sent=False, raise_exception=True)
        if sms.state == "error":
            reason = dict(
                sms._fields["failure_type"]._description_selection(self.env)
            ).get(sms.failure_type, _("Unknown error"))
            raise UserError(
                _(
                    "SMS to %(name)s failed: %(reason)s",
                    name=self.recipient_id.name,
                    reason=reason,
                )
            )
        _logger.info(
            "education_notification: SMS sent to %s (%s)",
            self.recipient_id.name,
            number,
        )

    def _send_inapp(self):
        """Send an in-app message as a Discuss direct chat to the recipient.

        Gets (or creates) the 1:1 chat channel between the sender and the
        recipient partner, then posts the notification body there. The
        recipient sees it as a normal Discuss conversation.
        """
        self.ensure_one()
        channel = self.env["discuss.channel"]._get_or_create_chat(
            partners_to=self.recipient_id.ids,
        )
        channel.message_post(
            body=self.body,
            subject=self.subject or _("Notification"),
            message_type="comment",
            subtype_xmlid="mail.mt_comment",
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
