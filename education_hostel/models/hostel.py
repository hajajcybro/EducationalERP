# -*- coding: utf-8 -*-
"""
education_hostel — Hostel Property, Room and Allocation models
==============================================================
Implements:
  - edu.hostel.property  (S6-T09)
  - edu.hostel.room      (S6-T10)
  - edu.hostel.allocation (S6-T11 / S6-T12)
"""
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class EduHostelProperty(models.Model):
    """A physical hostel building / block managed by the institution."""

    _name = "edu.hostel.property"
    _description = "Hostel Property"
    _order = "name"

    # ── Basic fields ──────────────────────────────────────────────────────
    name = fields.Char(string="Property Name", required=True)
    block = fields.Char(string="Block / Wing")
    total_capacity = fields.Integer(string="Total Capacity")
    warden_id = fields.Many2one(
        comodel_name="res.users",
        string="Warden",
        domain=[("share", "=", False)],
    )
    active = fields.Boolean(string="Active", default=True)

    # ── Rooms ─────────────────────────────────────────────────────────────
    room_ids = fields.One2many(
        comodel_name="edu.hostel.room",
        inverse_name="property_id",
        string="Rooms",
    )

    # ── Computed counts (stat buttons) ────────────────────────────────────
    room_count = fields.Integer(
        string="Rooms",
        compute="_compute_room_counts",
        store=True,
    )
    occupied_count = fields.Integer(
        string="Occupied",
        compute="_compute_room_counts",
        store=True,
    )

    @api.depends("room_ids", "room_ids.state")
    def _compute_room_counts(self):
        for rec in self:
            rec.room_count = len(rec.room_ids)
            rec.occupied_count = len(
                rec.room_ids.filtered(lambda r: r.state == "occupied")
            )


class EduHostelRoom(models.Model):
    """A single room inside a hostel property."""

    _name = "edu.hostel.room"
    _description = "Hostel Room"
    _order = "property_id, room_no"

    property_id = fields.Many2one(
        comodel_name="edu.hostel.property",
        string="Property",
        required=True,
        ondelete="cascade",
    )
    room_no = fields.Char(string="Room No.", required=True)
    room_type = fields.Selection(
        selection=[
            ("single", "Single"),
            ("double", "Double"),
            ("dormitory", "Dormitory"),
        ],
        string="Type",
        default="single",
        required=True,
    )
    capacity = fields.Integer(string="Capacity", default=1)
    amenities = fields.Text(string="Amenities")
    state = fields.Selection(
        selection=[
            ("available", "Available"),
            ("occupied", "Occupied"),
            ("maintenance", "Maintenance"),
        ],
        string="State",
        default="available",
        required=True,
        tracking=True,
    )
    active = fields.Boolean(string="Active", default=True)

    _sql_constraints = [
        (
            "unique_room_per_property",
            "UNIQUE(property_id, room_no)",
            "Room number must be unique within the same property.",
        ),
    ]


class EduHostelAllocation(models.Model):
    """Allocation of a student to a hostel room."""

    _name = "edu.hostel.allocation"
    _description = "Hostel Allocation"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "date_from desc, id desc"
    _rec_name = "enrollment_id"

    enrollment_id = fields.Many2one(
        comodel_name="education.enrollment",
        string="Enrollment",
        required=True,
        tracking=True,
    )
    room_id = fields.Many2one(
        comodel_name="edu.hostel.room",
        string="Room",
        required=True,
        tracking=True,
    )
    date_from = fields.Date(
        string="From Date",
        required=True,
        default=fields.Date.today,
        tracking=True,
    )
    date_to = fields.Date(
        string="To Date",
        tracking=True,
    )
    hostel_fee = fields.Float(
        string="Hostel Fee",
        default=0.0,
        tracking=True,
    )
    state = fields.Selection(
        selection=[
            ("draft", "Draft"),
            ("confirmed", "Confirmed"),
            ("vacated", "Vacated"),
        ],
        string="State",
        default="draft",
        required=True,
        tracking=True,
    )
    notes = fields.Text(string="Notes")

    # ── Constraints ───────────────────────────────────────────────────────

    @api.constrains("date_from", "date_to")
    def _check_dates(self):
        for rec in self:
            if rec.date_to and rec.date_from and rec.date_to < rec.date_from:
                raise ValidationError(
                    _("End date (%s) must be on or after start date (%s).")
                    % (rec.date_to, rec.date_from)
                )

    # ── Workflow actions ──────────────────────────────────────────────────

    def action_confirm(self):
        """Confirm allocation: mark room as occupied."""
        for rec in self:
            if rec.state != "draft":
                raise UserError(_("Only draft allocations can be confirmed."))

            # Check the student does not already have an active allocation
            duplicate = self.search(
                [
                    ("enrollment_id", "=", rec.enrollment_id.id),
                    ("state", "=", "confirmed"),
                    ("id", "!=", rec.id),
                ]
            )
            if duplicate:
                raise UserError(
                    _(
                        "Student '%s' already has a confirmed hostel allocation."
                    )
                    % rec.enrollment_id.display_name
                )

            rec.room_id.state = "occupied"
            rec.state = "confirmed"
            rec.message_post(
                body=_(
                    "Allocation confirmed. Room <b>%s</b> marked as occupied."
                )
                % rec.room_id.room_no
            )

    def action_vacate(self):
        """Vacate allocation: free the room."""
        for rec in self:
            if rec.state != "confirmed":
                raise UserError(_("Only confirmed allocations can be vacated."))
            rec.room_id.state = "available"
            rec.state = "vacated"
            rec.message_post(
                body=_(
                    "Allocation vacated. Room <b>%s</b> is now available."
                )
                % rec.room_id.room_no
            )

    def action_reset_draft(self):
        """Reset allocation back to draft."""
        for rec in self:
            if rec.state == "confirmed":
                # Free the room when resetting from confirmed
                rec.room_id.state = "available"
            rec.state = "draft"
            rec.message_post(body=_("Allocation reset to draft."))
