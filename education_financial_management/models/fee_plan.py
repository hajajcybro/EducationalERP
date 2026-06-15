# -*- coding: utf-8 -*-
"""
edu.fee.plan  — Fee plan header (S5-T01)
edu.fee.line  — Fee component lines within a plan
=========================================================
A fee plan is assigned to an enrollment. On activation the system
auto-generates an account.move (customer invoice) per fee line.
"""
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class EduFeePlan(models.Model):
    """Fee structure: collection of chargeable components for a programme/year."""

    _name = "edu.fee.plan"
    _description = "Fee Plan"
    _inherit = ["mail.thread"]
    _order = "academic_year_id desc, name"
    _rec_name = "name"

    currency_id = fields.Many2one(
        "res.currency",
        related="company_id.currency_id",
        depends=["company_id"],
        string="Currency",
        readonly=True,
    )
    company_id = fields.Many2one(
        "res.company",
        default=lambda self: self.env.company,
        readonly=True,
    )
    name = fields.Char(string="Plan Name", required=True, tracking=True)
    academic_year_id = fields.Many2one(
        "education.academic.year",
        string="Academic Year",
        required=True,
        index=True,
    )
    program_id = fields.Many2one(
        "education.program",
        string="Programme",
        help="Leave blank to apply to all programmes.",
    )
    class_ids = fields.Many2many(
        "education.class",
        "edu_fee_plan_class_rel",
        "fee_plan_id",
        "class_id",
        string="Applicable Classes",
        help="Leave blank to apply to all classes in the academic year.",
    )
    line_ids = fields.One2many(
        "edu.fee.line",
        "fee_plan_id",
        string="Fee Components",
    )
    total_amount = fields.Float(
        string="Total Amount",
        compute="_compute_total",
        store=True,
    )
    active = fields.Boolean(default=True)
    notes = fields.Text(string="Notes")

    @api.depends("line_ids.amount")
    def _compute_total(self):
        for rec in self:
            rec.total_amount = sum(rec.line_ids.mapped("amount"))

    @api.constrains("line_ids")
    def _check_lines(self):
        for rec in self:
            for line in rec.line_ids:
                if line.amount <= 0:
                    raise ValidationError(
                        _("Amount must be greater than zero for component '%s'.")
                        % line.component
                    )


class EduFeeLine(models.Model):
    """One chargeable component within a fee plan."""

    _name = "edu.fee.line"
    _description = "Fee Component"
    _order = "due_date, sequence"

    fee_plan_id = fields.Many2one(
        "edu.fee.plan",
        string="Fee Plan",
        required=True,
        ondelete="cascade",
        index=True,
    )
    sequence = fields.Integer(default=10)
    component = fields.Char(string="Component", required=True)
    fee_type = fields.Selection(
        selection=[
            ("tuition", "Tuition Fee"),
            ("lab", "Lab / Practical Fee"),
            ("library", "Library Fee"),
            ("transport", "Transport Fee"),
            ("hostel", "Hostel Fee"),
            ("exam", "Examination Fee"),
            ("activity", "Activity / Sports Fee"),
            ("other", "Other"),
        ],
        string="Type",
        required=True,
        default="tuition",
    )
    amount = fields.Float(string="Amount", required=True, default=0.0)
    due_date = fields.Date(string="Due Date")
    account_id = fields.Many2one(
        "account.account",
        string="Revenue Account",
        help="Income account for this fee component. "
             "If blank, the default income account will be used.",
        domain="[('account_type', 'like', 'income')]",
    )
    tax_ids = fields.Many2many(
        "account.tax",
        string="Taxes",
        domain="[('type_tax_use', '=', 'sale')]",
    )
