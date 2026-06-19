# -*- coding: utf-8 -*-
"""education.department — Academic department model."""
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class EducationDepartment(models.Model):
    """Academic department (e.g. Computer Science, Business Administration)."""

    _name = "education.department"
    _description = "Academic Department"
    _order = "sequence, name"
    _inherit = ["mail.thread"]

    name = fields.Char(
        string="Department Name",
        required=True,
        tracking=True,
        translate=True,
    )
    code = fields.Char(
        string="Code",
        required=True,
        size=10,
        tracking=True,
        help="Short code used in reports (e.g. CSE, MBA, MED).",
    )
    sequence = fields.Integer(default=10)
    head_id = fields.Many2one(
        "res.partner",
        string="Department Head",
        domain="[('is_company', '=', False)]",
        tracking=True,
    )
    description = fields.Text(string="Description")
    program_ids = fields.One2many(
        "education.program",
        "department_id",
        string="Programs",
    )
    program_count = fields.Integer(
        string="# Programs",
        compute="_compute_program_count",
    )
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        default=lambda self: self.env.company,
        required=True,
        index=True,
    )
    active = fields.Boolean(default=True)

    _code_company_uniq = models.Constraint(
            "UNIQUE(code, company_id)",
            "Department code must be unique per company.",
        )


    @api.depends("program_ids")
    def _compute_program_count(self):
        for rec in self:
            rec.program_count = len(rec.program_ids)

    def action_view_programs(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Programs — %s") % self.name,
            "res_model": "education.program",
            "domain": [("department_id", "=", self.id)],
            "view_mode": "list,form",
            "context": {"default_department_id": self.id},
        }
