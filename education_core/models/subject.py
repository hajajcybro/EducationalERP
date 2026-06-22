# -*- coding: utf-8 -*-
from odoo import models, fields


class EducationSubject(models.Model):
    """Subject / course within an academic program."""

    _name = "education.subject"
    _description = "Subject"
    _order = "program_id, sequence, name"

    name = fields.Char(string="Subject Name", required=True)
    code = fields.Char(string="Code", size=20)
    program_id = fields.Many2one(
        "education.program",
        string="Program",
        required=True,
        ondelete="cascade",
        index=True,
    )
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)

    _program_code_uniq = models.Constraint(
        "UNIQUE(program_id, code)",
        "Subject code must be unique within a program.",
    )
