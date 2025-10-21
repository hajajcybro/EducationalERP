# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import ValidationError


class EducationSession(models.Model):
    """ This model represents an Education Session for a given academic year. """
    _name = 'education.session'
    _description = 'Education Session'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'start_date asc'

    name = fields.Char(string="Session Name", required=True)
    code = fields.Char(string="Code")
    academic_year_id = fields.Many2one(
        'education.academic.year', string="Academic Year", required=True)  # Linked properly
    start_date = fields.Date(string="Start Date", required=True)
    end_date = fields.Date(string="End Date", required=True)
    sequence = fields.Integer(string="Sequence")
    is_current = fields.Boolean(string="Is Current Session", default=False)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('closed', 'Closed'),
    ], string="Status", default='draft', tracking=True)
    description = fields.Text(string="Description")
    active = fields.Boolean(default=True)

    duration_days = fields.Integer(string="Duration (Days)", compute="_compute_duration", store=True)

    _sql_constraints = [
        ('unique_session_per_year', 'unique(name, academic_year_id)', 'Session name must be unique per academic year.'),
    ]

    @api.depends('start_date', 'end_date')
    def _compute_duration(self):
        for rec in self:
            rec.duration_days = (rec.end_date - rec.start_date).days if rec.start_date and rec.end_date else 0


    @api.constrains('start_date', 'end_date')
    def _check_dates(self):
        for rec in self:
            if rec.start_date and rec.end_date and rec.start_date > rec.end_date:
                raise ValidationError("Start Date cannot be later than End Date.")

    def action_activate(self):
        """Mark the session as Active."""
        for rec in self:
            rec.state = 'active'

    def action_close(self):
        """Mark the session as Closed."""
        for rec in self:
            rec.state = 'closed'
