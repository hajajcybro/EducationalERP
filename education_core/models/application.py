# -*- coding: utf-8 -*-
"""
education.application — Student Admission Application
======================================================
State machine: draft → submitted → approved / rejected
On approval: auto-creates education.enrollment and portal account.
"""
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class EducationApplication(models.Model):
    """Student admission application with full state machine."""

    _name = "education.application"
    _description = "Student Application"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "date_application desc, admission_no desc"
    _rec_name = "admission_no"

    # ── Reference ────────────────────────────────────────────────────────
    admission_no = fields.Char(
        string="Application No.",
        readonly=True,
        copy=False,
        default="New",
        tracking=True,
    )
    state = fields.Selection(
        selection=[
            ("draft", "Draft"),
            ("submitted", "Submitted"),
            ("approved", "Approved"),
            ("rejected", "Rejected"),
        ],
        string="Status",
        default="draft",
        required=True,
        tracking=True,
    )
    date_application = fields.Date(
        string="Application Date",
        default=fields.Date.today,
        readonly=True,
    )

    # ── Personal Information ──────────────────────────────────────────────
    first_name = fields.Char(string="First Name", required=True, tracking=True)
    last_name = fields.Char(string="Last Name", tracking=True)
    name = fields.Char(
        string="Full Name",
        compute="_compute_name",
        store=True,
        help="Computed: First Name + Last Name.",
    )
    date_of_birth = fields.Date(string="Date of Birth", required=True)
    age = fields.Integer(
        string="Age",
        compute="_compute_age",
        store=False,
    )
    gender = fields.Selection(
        selection=[
            ("male", "Male"),
            ("female", "Female"),
            ("other", "Other / Prefer not to say"),
        ],
        string="Gender",
        required=True,
    )
    blood_group = fields.Selection(
        selection=[
            ("a+", "A+"), ("a-", "A−"),
            ("b+", "B+"), ("b-", "B−"),
            ("ab+", "AB+"), ("ab-", "AB−"),
            ("o+", "O+"), ("o-", "O−"),
        ],
        string="Blood Group",
    )
    nationality_id = fields.Many2one(
        "res.country",
        string="Nationality",
        default=lambda self: self.env.ref("base.in", raise_if_not_found=False),
    )
    photo = fields.Image(
        string="Passport Photo",
        max_width=256,
        max_height=256,
    )

    # ── Contact ───────────────────────────────────────────────────────────
    email = fields.Char(string="Email", required=True, tracking=True)
    phone = fields.Char(string="Phone", required=True)
    mobile = fields.Char(string="Mobile")
    address = fields.Text(string="Address")
    city = fields.Char(string="City")
    state_id = fields.Many2one(
        "res.country.state",
        string="State / Province",
        domain="[('country_id', '=', country_id)]",
    )
    country_id = fields.Many2one(
        "res.country",
        string="Country",
        default=lambda self: self.env.ref("base.in", raise_if_not_found=False),
    )
    zip_code = fields.Char(string="ZIP Code", size=10)

    # ── Academic Choice ───────────────────────────────────────────────────
    program_id = fields.Many2one(
        "education.program",
        string="Applied Program",
        required=True,
        tracking=True,
        ondelete="restrict",
    )
    academic_year_id = fields.Many2one(
        "education.academic.year",
        string="Academic Year",
        required=True,
        tracking=True,
        ondelete="restrict",
        default=lambda self: self.env["education.academic.year"].get_current_year(),
    )
    department_id = fields.Many2one(
        "education.department",
        string="Department",
        related="program_id.department_id",
        store=True,
        readonly=True,
    )

    # ── Previous Education ────────────────────────────────────────────────
    last_school = fields.Char(string="Last School / College")
    last_qualification = fields.Char(string="Qualification Obtained")
    last_percentage = fields.Float(
        string="Percentage / GPA",
        digits=(5, 2),
        help="Overall score in last qualification (0–100 or GPA scale).",
    )

    # ── Guardian / Parent ─────────────────────────────────────────────────
    guardian_name = fields.Char(string="Guardian Name", tracking=True)
    guardian_relation = fields.Selection(
        selection=[
            ("father", "Father"),
            ("mother", "Mother"),
            ("spouse", "Spouse"),
            ("sibling", "Sibling"),
            ("legal_guardian", "Legal Guardian"),
            ("other", "Other"),
        ],
        string="Relationship",
    )
    guardian_phone = fields.Char(string="Guardian Phone")
    guardian_email = fields.Char(string="Guardian Email")
    guardian_occupation = fields.Char(string="Guardian Occupation")

    # ── Documents O2M ─────────────────────────────────────────────────────
    document_ids = fields.One2many(
        "education.document",
        "application_id",
        string="Documents",
    )
    document_count = fields.Integer(
        string="Documents",
        compute="_compute_document_count",
    )

    # ── Rejection ─────────────────────────────────────────────────────────
    rejection_reason = fields.Text(string="Rejection Reason", readonly=True)
    rejected_by_id = fields.Many2one(
        "res.users",
        string="Rejected By",
        readonly=True,
    )
    rejection_date = fields.Date(string="Rejection Date", readonly=True)

    # ── Enrollment link (auto-created on approval) ────────────────────────
    enrollment_id = fields.Many2one(
        "education.enrollment",
        string="Enrollment",
        readonly=True,
        copy=False,
    )

    # ── System ────────────────────────────────────────────────────────────
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        default=lambda self: self.env.company,
        required=True,
        index=True,
    )
    active = fields.Boolean(default=True)
    notes = fields.Text(string="Internal Notes")

    _admission_no_uniq = models.Constraint (
            "UNIQUE(admission_no)",
            "Application number must be unique." )


    # ── ORM Overrides ─────────────────────────────────────────────────────

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("admission_no", "New") == "New":
                vals["admission_no"] = (
                    self.env["ir.sequence"].next_by_code("education.application")
                    or "New"
                )
        return super().create(vals_list)

    # ── Computed Fields ────────────────────────────────────────────────────

    @api.depends("first_name", "last_name")
    def _compute_name(self):
        for rec in self:
            parts = filter(None, [rec.first_name, rec.last_name])
            rec.name = " ".join(parts)

    @api.depends("date_of_birth")
    def _compute_age(self):
        today = fields.Date.today()
        for rec in self:
            if rec.date_of_birth:
                rec.age = (today - rec.date_of_birth).days // 365
            else:
                rec.age = 0

    @api.depends("document_ids")
    def _compute_document_count(self):
        for rec in self:
            rec.document_count = len(rec.document_ids)

    # ── Constraints ────────────────────────────────────────────────────────

    @api.constrains("date_of_birth")
    def _check_dob(self):
        today = fields.Date.today()
        for rec in self:
            if rec.date_of_birth and rec.date_of_birth >= today:
                raise ValidationError(
                    _("Date of Birth must be in the past for applicant '%s'.") % rec.name
                )

    @api.constrains("last_percentage")
    def _check_percentage(self):
        for rec in self:
            if rec.last_percentage and not (0 <= rec.last_percentage <= 100):
                raise ValidationError(
                    _("Percentage must be between 0 and 100 for applicant '%s'.") % rec.name
                )

    # ── State Machine Actions ──────────────────────────────────────────────

    def action_submit(self):
        """Student or Admission Officer submits the application."""
        for rec in self:
            if rec.state != "draft":
                raise ValidationError(
                    _("Only Draft applications can be submitted.")
                )
        self.write({"state": "submitted"})
        # Send acknowledgement email
        template = self.env.ref(
            "education_core.mail_template_application_received",
            raise_if_not_found=False,
        )
        if template:
            for rec in self:
                template.send_mail(rec.id, force_send=False)

    def action_approve(self):
        """Approve the application — auto-creates enrollment record."""
        for rec in self:
            if rec.state != "submitted":
                raise ValidationError(
                    _("Only Submitted applications can be approved.")
                )
            # Auto-create enrollment
            enrollment = self.env["education.enrollment"].create({
                "application_id": rec.id,
                "program_id": rec.program_id.id,
                "academic_year_id": rec.academic_year_id.id,
                "company_id": rec.company_id.id,
            })
            rec.write({"state": "approved", "enrollment_id": enrollment.id})
            # Carry the applicant's uploaded documents over to the enrollment
            # so they appear on the enrollment's Documents tab.
            if rec.document_ids:
                rec.document_ids.write({"enrollment_id": enrollment.id})
            # Send approval email
            template = self.env.ref(
                "education_core.mail_template_application_approved",
                raise_if_not_found=False,
            )
            if template:
                template.send_mail(rec.id, force_send=False)

    def action_reject(self):
        """Open rejection wizard."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Reject Application"),
            "res_model": "education.application.reject.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {"default_application_id": self.id},
        }

    def action_reset_draft(self):
        """Allow re-submission after rejection."""
        rejected = self.filtered(lambda r: r.state == "rejected")
        rejected.write({
            "state": "draft",
            "rejection_reason": False,
            "rejected_by_id": False,
            "rejection_date": False,
        })

    def action_view_enrollment(self):
        """Smart button to open the linked enrollment."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Enrollment — %s") % self.admission_no,
            "res_model": "education.enrollment",
            "res_id": self.enrollment_id.id,
            "view_mode": "form",
            "target": "current",
        }
