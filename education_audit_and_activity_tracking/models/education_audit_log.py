# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.tools import format_datetime


class EducationAuditLog(models.Model):
    _name = 'education.audit.log'
    _description = 'Education Audit Log'
    _order = 'timestamp desc'
    _rec_name = 'description'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    user_id = fields.Many2one(
        'res.users',
        string='User',
        required=True,
        default=lambda self: self.env.user,
        help='User who performed the action.'
    )

    action_type = fields.Selection(
        selection=[
            ('create', 'Create'),
            ('update', 'Update'),
            ('delete', 'Delete'),
            ('login', 'Login'),
            ('logout', 'Logout'),
            ('approval', 'Approval'),
            ('payment', 'Payment'),
        ],
        string='Action Type',
        required=True,
        help='Type of action performed.'
    )

    model_name = fields.Char(
        string='Model Name',
        required=True,
        help='Technical name of the affected model.'
    )

    record_id = fields.Integer(
        string='Record ID',
        help='ID of the affected record.'
    )

    description = fields.Text(
        string='Description',
        help='Human-readable description of the action.'
    )

    timestamp = fields.Datetime(
        string='Timestamp',
        default=fields.Datetime.now,
        index=True,
        help='Date and time when the action occurred.'
    )

    ip_address = fields.Char(
        string='IP Address',
        help='IP address from which the action was performed.'
    )

    old_values = fields.Json(
        string='Old Values',
        help='Previous values before the action.'
    )

    new_values = fields.Json(
        string='New Values',
        help='New values after the action.'
    )

