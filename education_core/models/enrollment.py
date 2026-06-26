# -*- coding: utf-8 -*-
"""
education.enrollment — Student Enrollment Record
=================================================
Created automatically when an admission application is approved.
Links student → class → academic year; manages portal accounts.
"""
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class EducationEnrollment(models.Model):
    """Student enrollment — one per student per academic year."""

    _name = "education.enrollment"
    _description = "Student Enrollment"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "enrollment_date desc, enrollment_no desc"
    _rec_name = "display_name"

    # ── Reference ────────────────────────────────────────────────────────
    enrollment_no = fields.Char(
        string="Enrollment No.",
        readonly=True,
        copy=False,
        default="New",
        tracking=True,
    )
    display_name = fields.Char(
        string="Display Name",
        compute="_compute_display_name",
        store=True,
        help="Shows student name + enrollment no. for easy identification.",
    )

    state = fields.Selection(
        selection=[
            ("active", "Active"),
            ("suspended", "Suspended"),
            ("graduated", "Graduated"),
            ("withdrawn", "Withdrawn"),
        ],
        string="Status",
        default="active",
        required=True,
        tracking=True,
    )
    enrollment_date = fields.Date(
        string="Enrollment Date",
        default=fields.Date.today,
        required=True,
    )

    # ── Application link ─────────────────────────────────────────────────
    application_id = fields.Many2one(
        "education.application",
        string="Application",
        required=True,
        ondelete="restrict",
        readonly=True,
        index=True,
    )

    # ── Student info (denormalised for fast display) ──────────────────────
    student_name = fields.Char(
        string="Student Name",
        related="application_id.name",
        store=True,
        readonly=True,
    )
    student_email = fields.Char(
        string="Student Email",
        related="application_id.email",
        store=True,
        readonly=True,
    )
    date_of_birth = fields.Date(
        string="Date of Birth",
        related="application_id.date_of_birth",
        store=True,
        readonly=True,
    )
    photo = fields.Image(
        string="Photo",
        related="application_id.photo",
        store=False,
        readonly=True,
    )

    # ── Guardian info (denormalised) ──────────────────────────────────────
    guardian_name = fields.Char(
        string="Guardian Name",
        related="application_id.guardian_name",
        store=True,
        readonly=True,
    )
    guardian_phone = fields.Char(
        string="Guardian Phone",
        related="application_id.guardian_phone",
        store=True,
        readonly=True,
    )
    guardian_email = fields.Char(
        string="Guardian Email",
        related="application_id.guardian_email",
        store=True,
        readonly=True,
    )

    # ── Academic placement ────────────────────────────────────────────────
    program_id = fields.Many2one(
        "education.program",
        string="Program",
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
    )
    class_id = fields.Many2one(
        "education.class",
        string="Class / Section",
        tracking=True,
        ondelete="restrict",
        domain="[('program_id', '=', program_id), "
               " ('academic_year_id', '=', academic_year_id)]",
    )
    department_id = fields.Many2one(
        "education.department",
        string="Department",
        related="program_id.department_id",
        store=True,
        readonly=True,
    )

    # ── Portal Accounts ───────────────────────────────────────────────────
    student_partner_id = fields.Many2one(
        "res.partner",
        string="Student Portal Account",
        readonly=True,
        copy=False,
        help="Created when portal access is granted.",
    )
    guardian_partner_id = fields.Many2one(
        "res.partner",
        string="Guardian Portal Account",
        readonly=True,
        copy=False,
    )

    # ── Documents ─────────────────────────────────────────────────────────
    document_ids = fields.One2many(
        "education.document",
        "enrollment_id",
        string="Documents",
    )
    document_count = fields.Integer(
        string="Documents",
        compute="_compute_document_count",
    )
    doc_completion_pct = fields.Integer(
        string="Doc Completion %",
        compute="_compute_doc_completion",
        help="Percentage of documents verified.",
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
    notes = fields.Text(string="Notes")

    _enrollment_no_uniq = models.Constraint(
        "UNIQUE(enrollment_no)",
        "Enrollment number must be unique.",
    )
    _application_year_uniq = models.Constraint(
        "UNIQUE(application_id, academic_year_id)",
        "A student can only be enrolled once per academic year.",
    )

    # ── ORM Overrides ─────────────────────────────────────────────────────

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("enrollment_no", "New") == "New":
                vals["enrollment_no"] = (
                    self.env["ir.sequence"].next_by_code("education.enrollment")
                    or "New"
                )
        return super().create(vals_list)

    # ── Computed ───────────────────────────────────────────────────────────
    #
    @api.depends("student_name", "enrollment_no")
    def _compute_display_name(self):
        for rec in self:
            if rec.student_name and rec.enrollment_no:
                rec.display_name = f"{rec.student_name} ({rec.enrollment_no})"
            else:
                rec.display_name = rec.enrollment_no or "New"

    @api.depends("document_ids")
    def _compute_document_count(self):
        for rec in self:
            rec.document_count = len(rec.document_ids)

    @api.depends("document_ids", "document_ids.state")
    def _compute_doc_completion(self):
        for rec in self:
            total = len(rec.document_ids)
            if not total:
                rec.doc_completion_pct = 0
            else:
                verified = rec.document_ids.filtered(
                    lambda d: d.state == "verified"
                )
                rec.doc_completion_pct = int(len(verified) / total * 100)

    # ── Actions ────────────────────────────────────────────────────────────

    def action_grant_portal_access(self):
        """Create res.partner for student and send portal invitation."""
        for rec in self:
            if rec.student_partner_id:
                raise UserError(
                    _("Portal access has already been granted for enrollment %s.")
                    % rec.enrollment_no)
            # Create partner
            partner = self.env["res.partner"].create({
                "name": rec.student_name,
                "email": rec.student_email,
                "is_company": False,
                "type": "contact",
                "comment": _("Auto-created for enrollment %s") % rec.enrollment_no,
            })
            rec.student_partner_id = partner
            # Send portal invite via Odoo wizard.
            # Odoo 19: 'in_portal' field and 'action_apply()' no longer exist.
            # Create wizard via partner_ids → user_ids is auto-computed by
            # _compute_user_ids, then call action_grant_access() on the user
            # record to create the portal user and send the invitation email.
            wizard = self.env["portal.wizard"].create({
                "partner_ids": [(4, partner.id)],
            })
            wizard_user = wizard.user_ids.filtered(
                lambda u: u.partner_id == partner
            )
            if wizard_user:
                wizard_user.action_grant_access()
            # Log in chatter
            rec.message_post(
                body=_("Portal access granted. Login invitation sent to %s.")
                % (partner.email or _("(no email)")),
            )

    def action_set_portal_password(self):
        """Open the wizard to set/reset the student's portal password.

        Admin-only: the header button is restricted to the education admin
        group. Lets staff hand a student a working password directly instead
        of relying on the invitation email being delivered.
        """
        self.ensure_one()
        if not self.student_partner_id:
            raise UserError(
                _("Grant portal access first — no portal account exists for "
                  "enrollment %s.") % self.enrollment_no)
        user = self.student_partner_id.user_ids[:1]
        if not user:
            raise UserError(
                _("No portal user is linked to this student yet. Use "
                  "'Grant Portal Access' first."))
        return {
            "type": "ir.actions.act_window",
            "name": _("Set Portal Password"),
            "res_model": "education.portal.password.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_enrollment_id": self.id,
                "default_user_id": user.id,
            },
        }

    def action_suspend(self):
        self.write({"state": "suspended"})

    def action_reactivate(self):
        self.write({"state": "active"})

    def action_graduate(self):
        self.write({"state": "graduated"})

    def action_withdraw(self):
        self.write({"state": "withdrawn"})

    def action_view_application(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Application"),
            "res_model": "education.application",
            "res_id": self.application_id.id,
            "view_mode": "form",
            "target": "current",
        }
