# -*- coding: utf-8 -*-
"""
education_config.models.institution_profile
===========================================
Singleton model that stores institution-level settings: name, branding,
contact details, academic calendar parameters and system configuration.

There is exactly ONE institution.profile record per company (enforced by
_sql_constraints).  Use InstitutionProfile.get_profile(env) to retrieve it.
"""
import pytz
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class InstitutionProfile(models.Model):
    """Institution-level configuration singleton."""

    _name = "institution.profile"
    _description = "Institution Profile"
    _order = "name"
    _rec_name = "name"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    # ── Identity ─────────────────────────────────────────────────────────
    name = fields.Char(
        string="Institution Name",
        required=True,
        tracking=True,
        help="Full legal name of the institution.",
    )
    short_name = fields.Char(
        string="Short Name / Abbreviation",
        size=20,
        tracking=True,
        help="Acronym or short form used in reports and emails.",
    )
    logo = fields.Image(
        string="Institution Logo",
        max_width=512,
        max_height=512,
        help="Square logo, minimum 256×256 px. Used in reports and portal.",
    )
    institution_type = fields.Selection(
        selection=[
            ("university", "University"),
            ("college", "College / Institute"),
            ("school", "School (K-12)"),
            ("vocational", "Vocational / Polytechnic"),
            ("corporate", "Corporate Training Centre"),
            ("healthcare", "Healthcare / Medical"),
            ("military", "Military / Defence"),
            ("other", "Other"),
        ],
        string="Institution Type",
        required=True,
        default="university",
        tracking=True,
    )
    registration_number = fields.Char(
        string="Registration / Accreditation No.",
        tracking=True,
    )
    established_year = fields.Integer(
        string="Established Year",
        help="Year the institution was founded.",
    )
    accreditation_body = fields.Char(
        string="Accreditation Body",
        help="e.g. NAAC, UGC, ISO 21001:2018",
    )

    # ── Branding ──────────────────────────────────────────────────────────
    branding_color = fields.Char(
        string="Primary Branding Colour",
        default="#1F3864",
        help="Hex colour used in reports, portal header and email templates.",
    )
    branding_color_secondary = fields.Char(
        string="Secondary Branding Colour",
        default="#2E75B6",
    )

    # ── Contact ───────────────────────────────────────────────────────────
    address = fields.Text(
        string="Address",
        tracking=True,
    )
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
    zip_code = fields.Char(string="ZIP / Postal Code", size=10)
    phone = fields.Char(string="Phone", tracking=True)
    mobile = fields.Char(string="Mobile / WhatsApp")
    email = fields.Char(string="Email", tracking=True)
    website = fields.Char(string="Website URL")

    # ── System ────────────────────────────────────────────────────────────
    timezone = fields.Selection(
        string="Timezone",
        selection="_tz_get",
        default=lambda self: self.env.user.tz or "UTC",
        required=True,
    )
    currency_id = fields.Many2one(
        "res.currency",
        string="Default Currency",
        default=lambda self: self.env.company.currency_id,
        required=True,
    )
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        default=lambda self: self.env.company,
        required=True,
    )
    active = fields.Boolean(default=True)

    # ── Academic Calendar Defaults ────────────────────────────────────────
    academic_year_start_month = fields.Selection(
        selection=[(str(m), n) for m, n in [
            (1, "January"), (2, "February"), (3, "March"), (4, "April"),
            (5, "May"), (6, "June"), (7, "July"), (8, "August"),
            (9, "September"), (10, "October"), (11, "November"), (12, "December"),
        ]],
        string="Academic Year Start Month",
        default="7",
        help="Month when a new academic year typically starts.",
    )
    working_days = fields.Selection(
        selection=[
            ("5", "Monday – Friday (5 days)"),
            ("6", "Monday – Saturday (6 days)"),
        ],
        string="Working Days per Week",
        default="5",
    )
    max_periods_per_day = fields.Integer(
        string="Max Periods per Day",
        default=8,
    )

    # ── SQL Constraints ───────────────────────────────────────────────────
    _sql_constraints = [
        (
            "unique_company",
            "UNIQUE(company_id)",
            "Only one Institution Profile is allowed per company.",
        )
    ]

    # ── Methods ───────────────────────────────────────────────────────────

    @api.model
    def _tz_get(self):
        """Return list of (tz, tz) tuples for the timezone Selection field."""
        return [
            (tz, tz)
            for tz in sorted(pytz.all_timezones, key=lambda z: z.lower())
        ]

    @api.model
    def get_profile(self):
        """
        Return the singleton profile for the current company.
        Creates a default one if it doesn't exist yet.
        """
        profile = self.search([("company_id", "=", self.env.company.id)], limit=1)
        if not profile:
            profile = self.create({
                "name": self.env.company.name,
                "company_id": self.env.company.id,
                "timezone": self.env.user.tz or "UTC",
                "currency_id": self.env.company.currency_id.id,
            })
        return profile

    def action_open_profile(self):
        """Smart button / menu action to open the profile form."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Institution Profile"),
            "res_model": "institution.profile",
            "res_id": self.id,
            "view_mode": "form",
            "target": "current",
        }

    @api.constrains("branding_color", "branding_color_secondary")
    def _check_hex_colour(self):
        import re
        hex_re = re.compile(r"^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$")
        for rec in self:
            for colour in (rec.branding_color, rec.branding_color_secondary):
                if colour and not hex_re.match(colour):
                    raise ValidationError(
                        _("Branding colour '%s' is not a valid hex value (e.g. #1F3864).")
                        % colour
                    )
