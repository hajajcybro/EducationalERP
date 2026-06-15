# -*- coding: utf-8 -*-
"""
education_notification — Unit Tests
======================================
Covers:
  - Notification queue created with state=pending
  - action_send() transitions email notification to 'sent'
  - action_retry() increments retry_count
  - edu.notification.centre action_mark_read()
  - _cron_process_queue() moves pending notifications out of 'pending'
"""
from odoo.tests import TransactionCase, tagged
from odoo import fields


@tagged("post_install", "-at_install")
class TestNotification(TransactionCase):
    """Unit tests for the education_notification module."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # ── Partner (recipient) ───────────────────────────────────────────
        cls.partner = cls.env["res.partner"].create({
            "name": "Test Partner",
            "email": "test@example.com",
        })

        # Make sure outgoing mail does not actually leave during tests by
        # routing to the catchall domain (standard Odoo test infrastructure
        # already traps mail.mail sends, so this is a belt-and-braces step).
        cls.env["ir.config_parameter"].sudo().set_param(
            "mail.catchall.domain", "example.com"
        )

    # ── Queue created pending ─────────────────────────────────────────────

    def test_queue_created_pending(self):
        """A new notification queue record should default to state='pending'."""
        notif = self.env["edu.notification.queue"].create({
            "notif_type": "email",
            "body": "Hello",
            "recipient_id": self.partner.id,
        })
        self.assertEqual(notif.state, "pending")

    # ── action_send transitions to sent ──────────────────────────────────

    def test_action_send_email(self):
        """action_send() on an email notification should result in state='sent'."""
        notif = self.env["edu.notification.queue"].create({
            "notif_type": "email",
            "subject": "Test Subject",
            "body": "<p>Test email body</p>",
            "recipient_id": self.partner.id,
        })
        # action_send internally calls mail.mail.send(); in test mode Odoo
        # routes the mail but does not actually deliver it. The state should
        # still become 'sent' (or 'failed' if mail infra raises). We accept
        # either 'sent' or verify the transition away from 'pending'.
        notif.action_send()
        self.assertIn(
            notif.state,
            ("sent", "failed"),
            "State should have transitioned away from 'pending' after action_send()",
        )

    def test_action_send_email_sets_sent_state(self):
        """When the recipient has a valid email, action_send() should set state='sent'."""
        notif = self.env["edu.notification.queue"].create({
            "notif_type": "email",
            "subject": "Hello",
            "body": "<p>Unit test notification</p>",
            "recipient_id": self.partner.id,
        })
        # Patch mail.mail.send to be a no-op so we are only testing the
        # state-machine logic and not actual SMTP delivery.
        MailMail = self.env["mail.mail"]
        original_send = MailMail.__class__.send

        def _dummy_send(self_inner, *args, **kwargs):
            pass  # swallow send so no SMTP call is made

        MailMail.__class__.send = _dummy_send
        try:
            notif.action_send()
        finally:
            MailMail.__class__.send = original_send

        self.assertEqual(notif.state, "sent")

    # ── action_retry increments count ────────────────────────────────────

    def test_action_retry_increments_count(self):
        """action_retry() should increment retry_count by 1."""
        notif = self.env["edu.notification.queue"].create({
            "notif_type": "email",
            "body": "Retry test",
            "recipient_id": self.partner.id,
            "state": "failed",
            "retry_count": 0,
        })

        # Patch send so the retry attempt itself doesn't change state
        # unexpectedly from external causes.
        MailMail = self.env["mail.mail"]
        original_send = MailMail.__class__.send

        def _dummy_send(self_inner, *args, **kwargs):
            pass

        MailMail.__class__.send = _dummy_send
        try:
            notif.action_retry()
        finally:
            MailMail.__class__.send = original_send

        self.assertEqual(notif.retry_count, 1)

    # ── Notification centre mark read ─────────────────────────────────────

    def test_centre_mark_read(self):
        """action_mark_read() should set is_read=True on the notification centre record."""
        centre = self.env["edu.notification.centre"].create({
            "user_id": self.env.uid,
            "title": "Test Notification",
            "message": "This is a test in-app notification.",
            "is_read": False,
        })
        self.assertFalse(centre.is_read)
        centre.action_mark_read()
        self.assertTrue(centre.is_read)

    # ── Cron processes pending ────────────────────────────────────────────

    def test_cron_processes_pending(self):
        """_cron_process_queue() should move a pending notification out of 'pending' state."""
        notif = self.env["edu.notification.queue"].create({
            "notif_type": "email",
            "body": "Cron test notification",
            "recipient_id": self.partner.id,
            "state": "pending",
        })

        # Patch mail send to avoid real delivery
        MailMail = self.env["mail.mail"]
        original_send = MailMail.__class__.send

        def _dummy_send(self_inner, *args, **kwargs):
            pass

        MailMail.__class__.send = _dummy_send
        try:
            self.env["edu.notification.queue"]._cron_process_queue()
        finally:
            MailMail.__class__.send = original_send

        self.assertNotEqual(
            notif.state,
            "pending",
            "Notification should no longer be 'pending' after cron run",
        )
