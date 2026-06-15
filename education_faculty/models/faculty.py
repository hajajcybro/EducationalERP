# -*- coding: utf-8 -*-
"""
education.faculty — Faculty Profile (S3-T11)
=============================================
Faculty member linked to an hr.employee record via delegation (_inherits).
Adds education-specific fields: faculty_id, department, specialization,
qualification history, and workload tracking.
"""
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

# Max weekly periods before overload alert
OVERLOAD_THRESHOLD = 30


class EducationFaculty(models.Model):
    """Faculty profile — extends hr.employee with academic fields."""

    _name = "education.faculty"
    _description = "Faculty Member"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "name"
    _rec_name = "name"

    # ── Identity ─────────────────────────────────────────────────────────
    name = fields.Char(
        string="Faculty Name",
        required=True,
        tracking=True,
    )
    faculty_id = fields.Char(
        string="Faculty ID",
        required=True,
        copy=False,
        default="New",
        tracking=True,
        help="Unique employee/faculty ID number.",
    )
    photo = fields.Image(
        string="Photo",
        max_width=256,
        max_height=256,
    )
    gender = fields.Selection(
        selection=[("male", "Male"), ("female", "Female"), ("other", "Other")],
        string="Gender",
    )
    date_of_birth = fields.Date(string="Date of Birth")
    blood_group = fields.Selection(
        selection=[
            ("a+", "A+"), ("a-", "A−"),
            ("b+", "B+"), ("b-", "B−"),
            ("ab+", "AB+"), ("ab-", "AB−"),
            ("o+", "O+"), ("o-", "O−"),
        ],
        string="Blood Group",
    )
    nationality_id = fields.Many2one("res.country", string="Nationality")

    # ── Contact ───────────────────────────────────────────────────────────
    email = fields.Char(string="Work Email", required=True, tracking=True)
    phone = fields.Char(string="Phone")
    mobile = fields.Char(string="Mobile")
    address = fields.Text(string="Address")

    # ── Academic Profile ──────────────────────────────────────────────────
    department_id = fields.Many2one(
        "education.department",
        string="Department",
        required=True,
        tracking=True,
        ondelete="restrict",
    )
    designation = fields.Char(
        string="Designation",
        help="e.g. Professor, Associate Professor, Lecturer.",
        tracking=True,
    )
    specialization = fields.Char(
        string="Specialization / Subject Area",
        tracking=True,
        help="Primary area of expertise.",
    )
    date_joined = fields.Date(
        string="Date Joined",
        default=fields.Date.today,
        tracking=True,
    )
    employment_type = fields.Selection(
        selection=[
            ("permanent", "Permanent"),
            ("contract", "Contract"),
            ("visiting", "Visiting / Adjunct"),
            ("part_time", "Part-time"),
        ],
        string="Employment Type",
        default="permanent",
        tracking=True,
    )

    # ── Qualifications ────────────────────────────────────────────────────
    qualification_ids = fields.One2many(
        "education.faculty.qualification",
        "faculty_id",
        string="Qualifications",
    )
    highest_qualification = fields.Char(
        string="Highest Qualification",
        compute="_compute_highest_qualification",
        store=True,
    )

    # ── Workload ──────────────────────────────────────────────────────────
    weekly_periods = fields.Integer(
        string="Assigned Weekly Periods",
        compute="_compute_weekly_periods",
        store=False,
        help="Total periods per week across all timetable slots assigned.",
    )
    is_overloaded = fields.Boolean(
        string="Overloaded",
        compute="_compute_weekly_periods",
        store=False,
        help=f"True when weekly periods exceed {OVERLOAD_THRESHOLD}.",
    )

    # ── HR Link (optional) ────────────────────────────────────────────────
    employee_id = fields.Many2one(
        "hr.employee",
        string="HR Employee Record",
        copy=False,
        ondelete="set null",
        help="Link to Odoo HR employee for payroll and leave integration.",
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

    _sql_constraints = [
        (
            "faculty_id_company_uniq",
            "UNIQUE(faculty_id, company_id)",
            "Faculty ID must be unique per company.",
        ),
        (
            "email_uniq",
            "UNIQUE(email, company_id)",
            "A faculty member with this email already exists in this company.",
        ),
    ]

    # ── ORM ───────────────────────────────────────────────────────────────

    @api.model_create_multi
    def create(self, vals_list):
        Seq = self.env["ir.sequence"]
        for vals in vals_list:
            if vals.get("faculty_id", "New") == "New":
                vals["faculty_id"] = Seq.next_by_code("education.faculty") or "New"
        return super().create(vals_list)

    # ── Computed ───────────────────────────────────────────────────────────

    @api.depends("qualification_ids", "qualification_ids.degree")
    def _compute_highest_qualification(self):
        degree_rank = {
            "phd": 5, "post_doc": 6,
            "master": 4, "bachelor": 3,
            "diploma": 2, "certificate": 1, "other": 0,
        }
        for rec in self:
            if not rec.qualification_ids:
                rec.highest_qualification = ""
                continue
            top = max(rec.qualification_ids,
                      key=lambda q: degree_rank.get(q.degree, 0))
            rec.highest_qualification = top.display_name

    def _compute_weekly_periods(self):
        Slot = self.env["education.timetable.slot"]
        for rec in self:
            # Count slots where this faculty member is assigned as teacher
            partner = self.env["res.partner"].search(
                [("email", "=", rec.email)], limit=1
            )
            if partner:
                periods = Slot.search_count([
                    ("teacher_id", "=", partner.id),
                    ("timetable_id.state", "=", "published"),
                ])
            else:
                periods = 0
            rec.weekly_periods = periods
            rec.is_overloaded = periods > OVERLOAD_THRESHOLD

    # ── Actions ────────────────────────────────────────────────────────────

    def action_view_timetable_slots(self):
        self.ensure_one()
        partner = self.env["res.partner"].search(
            [("email", "=", self.email)], limit=1
        )
        domain = [("teacher_id", "=", partner.id)] if partner else [("id", "=", 0)]
        return {
            "type": "ir.actions.act_window",
            "name": _("Timetable Slots — %s") % self.name,
            "res_model": "education.timetable.slot",
            "view_mode": "list",
            "domain": domain,
        }


class EducationFacultyQualification(models.Model):
    """Academic qualification entry for a faculty member (S3-T12)."""

    _name = "education.faculty.qualification"
    _description = "Faculty Qualification"
    _order = "year_obtained desc"

    faculty_id = fields.Many2one(
        "education.faculty",
        string="Faculty Member",
        required=True,
        ondelete="cascade",
        index=True,
    )
    degree = fields.Selection(
        selection=[
            ("certificate", "Certificate"),
            ("diploma", "Diploma"),
            ("bachelor", "Bachelor's Degree"),
            ("master", "Master's Degree"),
            ("phd", "PhD / Doctorate"),
            ("post_doc", "Post-Doctoral"),
            ("other", "Other"),
        ],
        string="Degree",
        required=True,
    )
    field_of_study = fields.Char(
        string="Field of Study",
        required=True,
        help="e.g. Computer Science, Mathematics, Physics.",
    )
    institution = fields.Char(
        string="Institution",
        required=True,
    )
    year_obtained = fields.Integer(
        string="Year Obtained",
        required=True,
    )
    grade = fields.Char(
        string="Grade / GPA",
        help="e.g. First Class, 9.2 CGPA.",
    )
    certificate_file = fields.Binary(string="Certificate", attachment=True)
    certificate_file_name = fields.Char()
    display_name = fields.Char(
        compute="_compute_display_name",
        store=True,
    )

    @api.depends("degree", "field_of_study", "institution", "year_obtained")
    def _compute_display_name(self):
        degree_labels = dict(self._fields["degree"].selection)
        for rec in self:
            rec.display_name = (
                f"{degree_labels.get(rec.degree, '')} in "
                f"{rec.field_of_study} — {rec.institution} ({rec.year_obtained})"
            )

    @api.constrains("year_obtained")
    def _check_year(self):
        import datetime
        current_year = datetime.date.today().year
        for rec in self:
            if rec.year_obtained and not (1900 <= rec.year_obtained <= current_year + 1):
                raise ValidationError(
                    _("Year obtained must be between 1900 and %d.") % current_year
                )
