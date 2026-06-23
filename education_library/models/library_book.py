# -*- coding: utf-8 -*-
"""
edu.library.book.category & edu.library.book
=============================================
S6-T01: Book catalogue model.
"""
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class EduLibraryBookCategory(models.Model):
    """Book category — groups books and carries the fine rate."""

    _name = "edu.library.book.category"
    _description = "Library Book Category"
    _order = "name"

    name = fields.Char(string="Category Name", required=True, translate=True)
    daily_fine_rate = fields.Float(
        string="Daily Fine Rate",
        default=1.0,
        help="Fine charged per overdue day (in company currency).",
    )
    book_ids = fields.One2many(
        "edu.library.book",
        "category_id",
        string="Books",
    )
    book_count = fields.Integer(
        string="Books",
        compute="_compute_book_count",
    )

    @api.depends("book_ids")
    def _compute_book_count(self):
        for rec in self:
            rec.book_count = len(rec.book_ids)


class EduLibraryBook(models.Model):
    """Library book — physical stock item in the catalogue."""

    _name = "edu.library.book"
    _description = "Library Book"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "title"
    _rec_name = "title"

    # ── Identification ───────────────────────────────────────────────────────
    isbn = fields.Char(
        string="ISBN",
        copy=False,
        index=True,
        help="International Standard Book Number (unique per title).",
    )
    title = fields.Char(string="Title", required=True, tracking=True)
    author = fields.Char(string="Author(s)", tracking=True)

    # ── Classification ───────────────────────────────────────────────────────
    category_id = fields.Many2one(
        "edu.library.book.category",
        string="Category",
        ondelete="set null",
        index=True,
        tracking=True,
    )
    rack_location = fields.Char(
        string="Rack / Location",
        help="Shelf or rack identifier in the physical library.",
    )

    # ── Stock ────────────────────────────────────────────────────────────────
    total_copies = fields.Integer(
        string="Total Copies",
        default=1,
        tracking=True,
    )
    available_copies = fields.Integer(
        string="Available Copies",
        compute="_compute_available_copies",
        store=True,
        tracking=True,
    )

    # ── Loans (inverse) ─────────────────────────────────────────────────────
    loan_ids = fields.One2many(
        "edu.library.loan",
        "book_id",
        string="Loans",
    )

    # ── System ───────────────────────────────────────────────────────────────
    active = fields.Boolean(default=True)
    notes = fields.Text(string="Notes")

    _isbn_uniq = models.Constraint(
            "UNIQUE(isbn)",
            "A book with this ISBN already exists.", ),


    # ── Computed ─────────────────────────────────────────────────────────────

    @api.depends("total_copies", "loan_ids", "loan_ids.state")
    def _compute_available_copies(self):
        for rec in self:
            active_loans = rec.loan_ids.filtered(
                lambda l: l.state in ("issued", "overdue"))
            rec.available_copies = max(0, rec.total_copies - len(active_loans))

    # ── Constraints ──────────────────────────────────────────────────────────

    @api.constrains("total_copies")
    def _check_total_copies(self):
        for rec in self:
            if rec.total_copies < 0:
                raise ValidationError(_("Total copies cannot be negative."))
