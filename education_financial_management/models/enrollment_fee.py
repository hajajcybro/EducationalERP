# -*- coding: utf-8 -*-
"""
Extends education.enrollment with fee management (S5-T02, S5-T03, S5-T04)
=========================================================================
- Adds fee_plan_id, invoice_ids, fee_state to enrollment
- Auto-generates account.move on generate_invoice() action
- Scholarship deduction applied as a credit line on the invoice
- Outstanding fee SQL view (S5-T08)
"""
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class EducationEnrollmentFee(models.Model):
    """Extend enrollment with fee plan + invoice link."""

    _inherit = "education.enrollment"

    # ── Fee plan ─────────────────────────────────────────────────────────
    fee_plan_id = fields.Many2one(
        "edu.fee.plan",
        string="Fee Plan",
        index=True,
        tracking=True,
    )
    scholarship_amount = fields.Float(
        string="Scholarship Deduction",
        default=0.0,
        help="Amount deducted from invoice as scholarship credit. (S5-T04)",
    )

    # ── Invoice link ──────────────────────────────────────────────────────
    invoice_ids = fields.One2many(
        "account.move",
        "enrollment_id",
        string="Fee Invoices",
        domain=[("move_type", "=", "out_invoice")],
    )
    invoice_count = fields.Integer(
        compute="_compute_invoice_info",
        string="Invoices",
    )
    fee_state = fields.Selection(
        selection=[
            ("not_invoiced", "Not Invoiced"),
            ("invoiced", "Invoiced"),
            ("partial", "Partially Paid"),
            ("paid", "Fully Paid"),
            ("overdue", "Overdue"),
        ],
        string="Fee Status",
        compute="_compute_invoice_info",
        store=True,
        default="not_invoiced",
    )
    total_fee = fields.Float(
        compute="_compute_invoice_info",
        string="Total Fee",
        store=True,
    )
    amount_paid = fields.Float(
        compute="_compute_invoice_info",
        string="Amount Paid",
        store=True,
    )
    amount_due = fields.Float(
        compute="_compute_invoice_info",
        string="Amount Due",
        store=True,
    )

    # ── Computed ──────────────────────────────────────────────────────────

    @api.depends(
        "invoice_ids",
        "invoice_ids.payment_state",
        "invoice_ids.amount_total",
        "invoice_ids.amount_residual",
    )
    def _compute_invoice_info(self):
        today = fields.Date.today()
        for rec in self:
            invoices = rec.invoice_ids.filtered(
                lambda i: i.state != "cancel"
            )
            rec.invoice_count = len(invoices)
            total = sum(invoices.mapped("amount_total"))
            residual = sum(invoices.mapped("amount_residual"))
            rec.total_fee = total
            rec.amount_paid = total - residual
            rec.amount_due = residual
            if not invoices:
                rec.fee_state = "not_invoiced"
            elif residual == 0:
                rec.fee_state = "paid"
            elif residual < total:
                rec.fee_state = "partial"
            elif any(
                i.invoice_date_due and i.invoice_date_due < today
                for i in invoices
                if i.payment_state not in ("paid", "in_payment")
            ):
                rec.fee_state = "overdue"
            else:
                rec.fee_state = "invoiced"

    # ── Actions ───────────────────────────────────────────────────────────

    def action_generate_invoice(self):
        """Create account.move (customer invoice) from fee plan (S5-T02)."""
        self.ensure_one()
        if not self.fee_plan_id:
            raise UserError(_("Assign a Fee Plan before generating an invoice."))
        if not self.student_partner_id:
            raise UserError(
                _("Student does not have a portal account. "
                  "Approve the application first.")
            )
        if self.invoice_ids.filtered(lambda i: i.state != "cancel"):
            raise UserError(
                _("An invoice already exists for this enrollment. "
                  "Cancel it first to re-generate.")
            )

        move_lines = []
        for line in self.fee_plan_id.line_ids:
            move_lines.append((0, 0, {
                "name": line.component,
                "quantity": 1,
                "price_unit": line.amount,
                "account_id": (
                    line.account_id.id
                    or self._get_default_income_account().id
                ),
                "tax_ids": [(6, 0, line.tax_ids.ids)],
            }))
        # Scholarship credit line (S5-T04)
        if self.scholarship_amount > 0:
            move_lines.append((0, 0, {
                "name": _("Scholarship Deduction"),
                "quantity": 1,
                "price_unit": -self.scholarship_amount,
                "account_id": self._get_default_income_account().id,
            }))
        invoice = self.env["account.move"].create({
            "move_type": "out_invoice",
            "partner_id": self.student_partner_id.id,
            "enrollment_id": self.id,
            "invoice_date": fields.Date.today(),
            "invoice_date_due": (
                self.fee_plan_id.line_ids.sorted("due_date")[-1].due_date
                if self.fee_plan_id.line_ids
                else False
            ),
            "narration": _(
                "Fee invoice for %s — %s"
            ) % (self.student_name, self.fee_plan_id.name),
            "invoice_line_ids": move_lines,
        })
        self.message_post(
            body=_("Fee invoice %s generated for %s (total: %.2f).")
            % (invoice.name, self.student_name, invoice.amount_total)
        )

        return {
            "type": "ir.actions.act_window",
            "name": _("Fee Invoice"),
            "res_model": "account.move",
            "res_id": invoice.id,
            "view_mode": "form",
            "target": "current",
        }

    def action_view_invoices(self):
        return {
            "type": "ir.actions.act_window",
            "name": _("Fee Invoices"),
            "res_model": "account.move",
            "view_mode": "list,form",
            "domain": [("enrollment_id", "=", self.id)],
        }

    def _get_default_income_account(self):
        """Return a sensible default income account."""
        account = self.env["account.account"].search([
            ("account_type", "=", "income"),
            ("company_ids", "in", self.env.company.id),
        ], limit=1)
        if not account:
            raise UserError(
                _("No income account found. Please configure your Chart of Accounts.")
            )
        return account


class AccountMove(models.Model):
    """Extend account.move with enrollment link (S5-T02)."""

    _inherit = "account.move"

    enrollment_id = fields.Many2one(
        "education.enrollment",
        string="Student Enrollment",
        index=True,
        ondelete="set null",
    )
    student_name = fields.Char(
        related="enrollment_id.student_name",
        store=True,
        readonly=True,
        string="Student",
    )
    class_id = fields.Many2one(
        "education.class",
        related="enrollment_id.class_id",
        store=True,
        readonly=True,
    )
    academic_year_id = fields.Many2one(
        "education.academic.year",
        related="enrollment_id.academic_year_id",
        store=True,
        readonly=True,
    )


class EduFeeOutstandingReport(models.Model):
    """SQL view — all active enrollments with outstanding fees (S5-T08)."""

    _name = "edu.fee.outstanding"
    _description = "Outstanding Fee Report"
    _auto = False
    _order = "amount_due desc"

    enrollment_id = fields.Many2one("education.enrollment", string="Enrollment", readonly=True)
    student_name = fields.Char(string="Student", readonly=True)
    class_id = fields.Many2one("education.class", string="Class", readonly=True)
    academic_year_id = fields.Many2one("education.academic.year", string="Year", readonly=True)
    fee_plan_id = fields.Many2one("edu.fee.plan", string="Fee Plan", readonly=True)
    total_fee = fields.Float(string="Total Fee", readonly=True)
    amount_paid = fields.Float(string="Paid", readonly=True)
    amount_due = fields.Float(string="Outstanding", readonly=True)
    fee_state = fields.Char(string="Status", readonly=True)
    invoice_date_due = fields.Date(string="Due Date", readonly=True)

    def init(self):
        self.env.cr.execute("""
            DROP VIEW IF EXISTS edu_fee_outstanding;
            CREATE VIEW edu_fee_outstanding AS (
                SELECT
                    e.id                        AS id,
                    e.id                        AS enrollment_id,
                    e.student_name              AS student_name,
                    e.class_id                  AS class_id,
                    e.academic_year_id          AS academic_year_id,
                    e.fee_plan_id               AS fee_plan_id,
                    COALESCE(e.total_fee, 0)    AS total_fee,
                    COALESCE(e.amount_paid, 0)  AS amount_paid,
                    COALESCE(e.amount_due, 0)   AS amount_due,
                    e.fee_state                 AS fee_state,
                    MIN(am.invoice_date_due)    AS invoice_date_due
                FROM education_enrollment e
                LEFT JOIN account_move am
                    ON am.enrollment_id = e.id
                    AND am.move_type = 'out_invoice'
                    AND am.state != 'cancel'
                WHERE e.state = 'active'
                  AND COALESCE(e.amount_due, 0) > 0
                GROUP BY e.id, e.student_name, e.class_id,
                         e.academic_year_id, e.fee_plan_id,
                         e.total_fee, e.amount_paid, e.amount_due, e.fee_state
            )
        """)
