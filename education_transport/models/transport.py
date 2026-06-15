# -*- coding: utf-8 -*-
"""
Education ERP — Transport Models
=================================
S6-T14: edu.transport.vehicle
S6-T15: edu.transport.route, edu.transport.stop
S6-T16: edu.transport.assignment
"""
from odoo import models, fields, api


class EduTransportRoute(models.Model):
    """Bus/van route definition."""

    _name = "edu.transport.route"
    _description = "Transport Route"
    _order = "name"

    name = fields.Char(string="Route Name", required=True)
    description = fields.Text(string="Description")
    active = fields.Boolean(string="Active", default=True)

    stop_ids = fields.One2many(
        "edu.transport.stop",
        "route_id",
        string="Stops",
    )
    stop_count = fields.Integer(
        string="Stops",
        compute="_compute_stop_count",
        store=True,
    )
    vehicle_ids = fields.One2many(
        "edu.transport.vehicle",
        "route_id",
        string="Vehicles",
    )

    @api.depends("stop_ids")
    def _compute_stop_count(self):
        for rec in self:
            rec.stop_count = len(rec.stop_ids)

    def action_view_stops(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Stops",
            "res_model": "edu.transport.stop",
            "view_mode": "list",
            "domain": [("route_id", "=", self.id)],
            "context": {"default_route_id": self.id},
        }


class EduTransportStop(models.Model):
    """Individual pickup/drop stop on a route."""

    _name = "edu.transport.stop"
    _description = "Transport Stop"
    _order = "route_id, sequence, name"

    name = fields.Char(string="Stop Name", required=True)
    route_id = fields.Many2one(
        "edu.transport.route",
        string="Route",
        required=True,
        ondelete="cascade",
        index=True,
    )
    sequence = fields.Integer(string="Sequence", default=10)
    pickup_time = fields.Float(
        string="Pickup Time",
        help="24-hour format, e.g. 7.5 = 07:30",
    )
    drop_time = fields.Float(
        string="Drop Time",
        help="24-hour format, e.g. 15.75 = 15:45",
    )
    distance_km = fields.Float(string="Distance (km)")


class EduTransportVehicle(models.Model):
    """School vehicle / bus fleet record."""

    _name = "edu.transport.vehicle"
    _description = "Transport Vehicle"
    _order = "registration_no"

    registration_no = fields.Char(
        string="Registration No.",
        required=True,
        copy=False,
    )
    make_model = fields.Char(string="Make / Model")
    capacity = fields.Integer(string="Capacity (seats)", default=40)
    driver_id = fields.Many2one(
        "res.partner",
        string="Driver",
        domain=[("is_company", "=", False)],
    )
    condition = fields.Selection(
        selection=[
            ("good", "Good"),
            ("fair", "Fair"),
            ("poor", "Poor"),
        ],
        string="Condition",
        default="good",
        required=True,
    )
    last_service_date = fields.Date(string="Last Service Date")
    route_id = fields.Many2one(
        "edu.transport.route",
        string="Assigned Route",
    )
    active = fields.Boolean(string="Active", default=True)

    _sql_constraints = [
        (
            "registration_no_uniq",
            "UNIQUE(registration_no)",
            "Registration number must be unique.",
        ),
    ]


class EduTransportAssignment(models.Model):
    """Links a student enrollment to a transport route/stop for a given year."""

    _name = "edu.transport.assignment"
    _description = "Student Transport Assignment"
    _order = "academic_year_id desc, route_id, stop_id"
    _rec_name = "student_name"

    enrollment_id = fields.Many2one(
        "education.enrollment",
        string="Enrollment",
        required=True,
        ondelete="restrict",
        index=True,
    )
    route_id = fields.Many2one(
        "edu.transport.route",
        string="Route",
        required=True,
        ondelete="restrict",
    )
    stop_id = fields.Many2one(
        "edu.transport.stop",
        string="Stop",
        required=True,
        ondelete="restrict",
        domain="[('route_id', '=', route_id)]",
    )
    academic_year_id = fields.Many2one(
        "education.academic.year",
        string="Academic Year",
        required=True,
        ondelete="restrict",
        index=True,
    )
    transport_fee = fields.Float(string="Transport Fee", default=0.0)
    state = fields.Selection(
        selection=[
            ("active", "Active"),
            ("inactive", "Inactive"),
        ],
        string="State",
        default="active",
        required=True,
    )

    # ── Related / denormalised ─────────────────────────────────────────────
    student_name = fields.Char(
        string="Student Name",
        related="enrollment_id.student_name",
        store=True,
        readonly=True,
    )
    class_id = fields.Many2one(
        "education.class",
        string="Class / Section",
        related="enrollment_id.class_id",
        store=True,
        readonly=True,
    )

    _sql_constraints = [
        (
            "enrollment_year_uniq",
            "UNIQUE(enrollment_id, academic_year_id)",
            "A student can only have one transport assignment per academic year.",
        ),
    ]
