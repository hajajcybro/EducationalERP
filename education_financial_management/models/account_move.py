from odoo import models, fields,api,_
from datetime import timedelta
from odoo.tools.misc import formatLang

class AccountMove(models.Model):
    _inherit = 'account.move'

    fee_invoice_id = fields.Many2one(
        'education.fee.invoice',
        string='Education Fee Invoice',
        ondelete='set null'
    )

    @api.model
    def _cron_send_due_tomorrow_reminder(self):
        """
        Send automated email reminders to student partners for posted customer invoices
        with an outstanding balance that are due tomorrow.
        """
        today = fields.Date.today()
        tomorrow = today + timedelta(days=1)
        invoices = self.search([
            ('move_type', '=', 'out_invoice'),
            ('state', '=', 'posted'),
            ('amount_residual', '>', 0),
        ])
        for invoice in invoices:
            partner = invoice.partner_id
            if partner and partner.is_student:
                due_dates = invoice.line_ids.mapped('date_maturity')
                due_dates = [d for d in due_dates if d] or [invoice.invoice_date_due]
                if tomorrow in due_dates:
                    email_from = ( invoice.company_id.email
                            or self.env.user.company_id.email)
                    amount = formatLang(
                        self.env,invoice.amount_residual,
                        currency_obj=invoice.currency_id
                    )
                    subject = _("Payment Reminder: Invoice %s") % (invoice.name or '')
                    body = _(
                        f"Dear {partner.name}, "
                        f"This is a gentle reminder that your invoice {invoice.name or ''} "
                        f"with an outstanding amount of {amount} is due tomorrow. "
                        f"Due Date: {invoice.invoice_date_due}."
                        f" Thank you."
                    )
                    invoice.message_post(
                        subject=subject,
                        body=body,
                        email_from=email_from,
                        partner_ids=[partner.id],
                        message_type='email',
                        subtype_xmlid='mail.mt_comment',
                    )