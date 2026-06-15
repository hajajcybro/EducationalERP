# -*- coding: utf-8 -*-
"""
edu.library.issue.wizard
=========================
S6-T05: Wizard to issue or return a library book.
"""
import datetime
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class EduLibraryIssueWizard(models.TransientModel):
    """Wizard — issue a book to a member or process a return."""

    _name = "edu.library.issue.wizard"
    _description = "Library Issue / Return Wizard"

    member_id = fields.Many2one(
        "edu.library.member",
        string="Member",
        required=True,
    )
    book_id = fields.Many2one(
        "edu.library.book",
        string="Book",
        required=True,
        domain=[("active", "=", True)],
    )
    action = fields.Selection(
        selection=[
            ("issue", "Issue"),
            ("return", "Return"),
        ],
        string="Action",
        required=True,
        default="issue",
    )
    due_date = fields.Date(
        string="Due Date",
        default=lambda self: fields.Date.today() + datetime.timedelta(days=14),
    )

    # ── Onchange / constraints ────────────────────────────────────────────────

    @api.onchange("action")
    def _onchange_action(self):
        if self.action == "return":
            self.due_date = False

    @api.constrains("action", "due_date")
    def _check_due_date(self):
        for rec in self:
            if rec.action == "issue" and not rec.due_date:
                raise ValidationError(_("Due date is required when issuing a book."))
            if rec.action == "issue" and rec.due_date and rec.due_date < fields.Date.today():
                raise ValidationError(_("Due date must be today or in the future."))

    # ── Confirm ───────────────────────────────────────────────────────────────

    def action_confirm(self):
        self.ensure_one()

        if self.action == "issue":
            self._do_issue()
        else:
            self._do_return()

        return {"type": "ir.actions.act_window_close"}

    def _do_issue(self):
        """Create a new loan for the member."""
        member = self.member_id
        book = self.book_id

        # Check availability
        if book.available_copies <= 0:
            raise UserError(
                _("Book '%s' has no available copies.", book.title)
            )

        # Check borrowing limit
        if member.active_loans_count >= member.borrowing_limit:
            raise UserError(
                _(
                    "Member %s has reached their borrowing limit of %d books.",
                    member.member_no,
                    member.borrowing_limit,
                )
            )

        self.env["edu.library.loan"].create({
            "book_id": book.id,
            "member_id": member.id,
            "issue_date": fields.Date.today(),
            "due_date": self.due_date,
            "state": "issued",
        })

    def _do_return(self):
        """Return the most recent active loan for the book+member pair."""
        loan = self.env["edu.library.loan"].search(
            [
                ("book_id", "=", self.book_id.id),
                ("member_id", "=", self.member_id.id),
                ("state", "in", ("issued", "overdue")),
            ],
            order="issue_date desc",
            limit=1,
        )
        if not loan:
            raise UserError(
                _(
                    "No active loan found for member %s and book '%s'.",
                    self.member_id.member_no,
                    self.book_id.title,
                )
            )
        loan.action_return()
