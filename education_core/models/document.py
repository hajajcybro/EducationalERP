# -*- coding: utf-8 -*-
"""
education.document.type — Configurable document types (Birth Certificate, etc.)
education.document      — Uploaded student document with verification workflow
"""
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class EducationDocumentType(models.Model):
    """Master list of document types required during admission."""

    _name = "education.document.type"
    _description = "Document Type"
    _order = "sequence, name"

    name = fields.Char(
        string="Document Type",
        required=True,
        translate=True,
    )
    code = fields.Char(
        string="Code",
        size=20,
        help="Short code, e.g. BIRTH_CERT, MARK_SHEET.",
    )
    sequence = fields.Integer(default=10)
    is_mandatory = fields.Boolean(
        string="Mandatory",
        default=False,
        help="If checked, applicants must upload this document before approval.",
    )
    description = fields.Text(
        string="Description / Instructions",
        translate=True,
    )
    active = fields.Boolean(default=True)

    _sql_constraints = [
        (
            "code_uniq",
            "UNIQUE(code)",
            "Document type code must be unique.",
        )
    ]


class EducationDocument(models.Model):
    """A single document uploaded by or for a student."""

    _name = "education.document"
    _description = "Student Document"
    _inherit = ["mail.thread"]
    _order = "document_type_id, id"

    name = fields.Char(
        string="Document Reference",
        compute="_compute_name",
        store=True,
    )

    # ── Links (one of these will be set) ──────────────────────────────────
    application_id = fields.Many2one(
        "education.application",
        string="Application",
        ondelete="cascade",
        index=True,
    )
    enrollment_id = fields.Many2one(
        "education.enrollment",
        string="Enrollment",
        ondelete="cascade",
        index=True,
    )

    # ── Document details ──────────────────────────────────────────────────
    document_type_id = fields.Many2one(
        "education.document.type",
        string="Document Type",
        required=True,
        ondelete="restrict",
    )
    is_mandatory = fields.Boolean(
        string="Mandatory",
        related="document_type_id.is_mandatory",
        store=True,
        readonly=True,
    )

    # ── File ──────────────────────────────────────────────────────────────
    file = fields.Binary(
        string="File",
        attachment=True,
        help="Upload PDF, JPG, or PNG (max 10 MB).",
    )
    file_name = fields.Char(string="File Name")

    # ── Validity ──────────────────────────────────────────────────────────
    issue_date = fields.Date(string="Issue Date")
    expiry_date = fields.Date(string="Expiry Date")

    # ── Verification workflow ─────────────────────────────────────────────
    state = fields.Selection(
        selection=[
            ("pending", "Pending Upload"),
            ("uploaded", "Uploaded — Pending Review"),
            ("verified", "Verified"),
            ("rejected", "Rejected / Resubmit"),
        ],
        string="Status",
        default="pending",
        required=True,
        tracking=True,
    )
    verified_by_id = fields.Many2one(
        "res.users",
        string="Verified By",
        readonly=True,
    )
    verified_date = fields.Date(string="Verified On", readonly=True)
    remarks = fields.Text(
        string="Remarks",
        help="Reviewer notes / rejection reason.",
    )

    # ── System ────────────────────────────────────────────────────────────
    active = fields.Boolean(default=True)

    # ── Computed ───────────────────────────────────────────────────────────

    @api.depends(
        "document_type_id.name",
        "application_id.admission_no",
        "enrollment_id.enrollment_no",
    )
    def _compute_name(self):
        for rec in self:
            ref = (
                rec.application_id.admission_no
                or rec.enrollment_id.enrollment_no
                or "—"
            )
            doc_type = rec.document_type_id.name or _("Document")
            rec.name = f"{doc_type} [{ref}]"

    # ── Constraints ────────────────────────────────────────────────────────

    @api.constrains("file", "state")
    def _check_file_on_upload(self):
        for rec in self:
            if rec.state in ("uploaded", "verified") and not rec.file:
                raise ValidationError(
                    _("Document '%s' must have a file attached before marking as uploaded.")
                    % rec.document_type_id.name
                )

    @api.constrains("issue_date", "expiry_date")
    def _check_dates(self):
        for rec in self:
            if rec.issue_date and rec.expiry_date and rec.expiry_date <= rec.issue_date:
                raise ValidationError(
                    _("Expiry Date must be after Issue Date for document '%s'.")
                    % rec.document_type_id.name
                )

    # ── Actions ────────────────────────────────────────────────────────────

    def action_mark_uploaded(self):
        for rec in self:
            if not rec.file:
                raise ValidationError(
                    _("Please attach a file before marking '%s' as uploaded.")
                    % rec.document_type_id.name
                )
        self.write({"state": "uploaded"})

    def action_verify(self):
        self.write({
            "state": "verified",
            "verified_by_id": self.env.uid,
            "verified_date": fields.Date.today(),
        })

    def action_reject_doc(self):
        self.write({"state": "rejected"})
