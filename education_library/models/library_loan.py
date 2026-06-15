# -*- coding: utf-8 -*-
"""
edu.library.loan & edu.library.cron
=====================================
S6-T03: Loan state machine (issued → returned / overdue).
S6-T04: Fine calculation.
S6-T06: Daily cron — due-date reminder email.
"""
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class EduLibraryLoan(models.Model):
    """A single book borrowing transaction."""

    _name = "edu.library.loan"
    _description = "Library Loan"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "issue_date desc, id desc"
    _rec_name = "display_name"

    # ── Core fields ───────────────────────────────────────────────────────────
    book_id = fields.Many2one(
        "edu.library.book",
        string="Book",
        required=True,
        ondelete="restrict",
        index=True,
        tracking=True,
    )
    member_id = fields.Many2one(
        "edu.library.member",
        string="Member",
        required=True,
        ondelete="restrict",
        index=True,
        tracking=True,
    )

    # ── Dates ─────────────────────────────────────────────────────────────────
    issue_date = fields.Date(
        string="Issue Date",
        default=fields.Date.today,
        required=True,
        tracking=True,
    )
    due_date = fields.Date(
        string="Due Date",
        required=True,
        tracking=True,
    )
    return_date = fields.Date(
        string="Return Date",
        tracking=True,
        copy=False,
    )

    # ── Fine ──────────────────────────────────────────────────────────────────
    fine_amount = fields.Float(
        string="Fine Amount",
        compute="_compute_fine_amount",
        store=True,
        tracking=True,
        digits=(16, 2),
    )

    # ── State ─────────────────────────────────────────────────────────────────
    state = fields.Selection(
        selection=[
            ("issued", "Issued"),
            ("overdue", "Overdue"),
            ("returned", "Returned"),
        ],
        string="Status",
        default="issued",
        required=True,
        tracking=True,
        index=True,
    )

    # ── Extra ─────────────────────────────────────────────────────────────────
    notes = fields.Text(string="Notes")

    # ── Display name ─────────────────────────────────────────────────────────

    @api.depends("book_id", "member_id", "issue_date")
    def _compute_display_name(self):
        for rec in self:
            book = rec.book_id.title or ""
            member = rec.member_id.member_no or ""
            rec.display_name = f"{book} / {member}"

    # ── Fine computation ──────────────────────────────────────────────────────

    @api.depends(
        "due_date",
        "return_date",
        "state",
        "book_id.category_id.daily_fine_rate",
    )
    def _compute_fine_amount(self):
        today = fields.Date.today()
        for rec in self:
            if not rec.due_date:
                rec.fine_amount = 0.0
                continue
            reference_date = rec.return_date or today
            overdue_days = (reference_date - rec.due_date).days
            rate = rec.book_id.category_id.daily_fine_rate if rec.book_id.category_id else 1.0
            rec.fine_amount = max(0, overdue_days) * rate

    # ── Actions ───────────────────────────────────────────────────────────────

    def action_return(self):
        """Mark the loan as returned: set return_date, update book stock."""
        today = fields.Date.today()
        for rec in self:
            if rec.state == "returned":
                raise UserError(_("Loan %s is already returned.", rec.display_name))
            rec.write({
                "return_date": today,
                "state": "returned",
            })
            # Recompute fine now that return_date is set
            rec._compute_fine_amount()
        return True

    def action_mark_overdue(self):
        """Mark loan as overdue (can be called manually or by cron)."""
        for rec in self:
            if rec.state == "issued":
                rec.state = "overdue"
        return True

    # ── Constraints ───────────────────────────────────────────────────────────

    @api.constrains("due_date", "issue_date")
    def _check_dates(self):
        for rec in self:
            if rec.due_date and rec.issue_date and rec.due_date < rec.issue_date:
                raise ValidationError(
                    _("Due date cannot be earlier than the issue date.")
                )

    @api.constrains("book_id", "state")
    def _check_book_availability(self):
        for rec in self:
            if rec.state in ("issued", "overdue"):
                if rec.book_id.available_copies < 0:
                    raise ValidationError(
                        _("Book '%s' is not available for borrowing.", rec.book_id.title)
                    )


class EduLibraryCron(models.AbstractModel):
    """Abstract model that carries the cron method for due-date reminders."""

    _name = "edu.library.cron"
    _description = "Library Cron Jobs"

    @api.model
    def _cron_due_date_reminder(self):
        """
        S6-T06: Daily cron — find loans due in 2 days and email the member.
        """
        import datetime
        target_date = fields.Date.today() + datetime.timedelta(days=2)
        loans = self.env["edu.library.loan"].search([
            ("due_date", "=", target_date),
            ("state", "in", ("issued", "overdue")),
        ])
        template = self.env.ref(
            "education_library.mail_template_loan_due",
            raise_if_not_found=False,
        )
        if not template:
            return
        for loan in loans:
            # Only send if we have a partner to send to
            partner = loan.member_id.student_partner_id
            if partner and partner.email:
                template.send_mail(loan.id, force_send=False)
