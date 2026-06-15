# -*- coding: utf-8 -*-
"""
edu.fee.overdue.cron — Daily cron: overdue fee reminders (S5-T05)
==================================================================
Finds all active enrollment invoices past due_date with unpaid balance
and sends an email reminder to the student's guardian.
"""
from odoo import models, fields, api, _


class EduFeeOverdueCron(models.AbstractModel):
    _name = "edu.fee.overdue.cron"
    _description = "Fee Overdue Cron"

    @api.model
    def _cron_send_overdue_reminders(self):
        """Called daily by ir.cron. Sends reminders for overdue fee invoices."""
        today = fields.Date.today()
        overdue_invoices = self.env["account.move"].search([
            ("move_type", "=", "out_invoice"),
            ("state", "=", "posted"),
            ("payment_state", "not in", ["paid", "in_payment"]),
            ("invoice_date_due", "<", today),
            ("enrollment_id", "!=", False),
        ])

        template = self.env.ref(
            "education_financial_management.mail_template_fee_overdue",
            raise_if_not_found=False,
        )

        sent = 0
        for invoice in overdue_invoices:
            enr = invoice.enrollment_id
            if not enr:
                continue
            # Update enrollment fee_state
            if enr.fee_state != "overdue":
                enr.fee_state = "overdue"

            if template and (
                enr.guardian_partner_id or enr.student_partner_id
            ):
                try:
                    template.send_mail(invoice.id, force_send=False)
                    sent += 1
                except Exception:
                    pass

        return _("Overdue fee reminders queued for %d invoices.") % sent
