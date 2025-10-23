# -*- coding: utf-8 -*-
from odoo import api, fields, models,_
from odoo.exceptions import ValidationError


class EducationAcademicYear(models.Model):
    """ This model represents education.academic.year."""
    _name = 'education.academic.year'
    _description = 'EducationAcademicYear'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'start_date desc'


    name = fields.Char(string='Academic Year', unique=True)
    start_date = fields.Date(string='Start Date', required=True)
    end_date = fields.Date(string='End Date', required=True)
    duration = fields.Char(string='Duration', compute='_compute_duration', store=True,
                           help='Displays academic year duration in format like 2024 → 2025')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('closed', 'Closed')
    ], string='Status', default='draft')
    is_current = fields.Boolean(string='Current Year', default=False,
                                help='Marks the current academic year.')
    active = fields.Boolean(string='Active', default=True)
    notes = fields.Text(string='Notes')

    _sql_constraints = [
        ('name_unique', 'unique(name)', 'The Academic Year name must be unique.'),
    ]

    @api.constrains('start_date', 'end_date')
    def _check_dates(self):
        for record in self:
            if record.start_date > record.end_date:
                raise ValidationError("Start date must be before end date.")


    @api.depends('start_date', 'end_date')
    def _compute_duration(self):
        """Compute duration in readable academic-year format."""
        for rec in self:
            if rec.start_date and rec.end_date:
                rec.duration = rec.end_date.year - rec.start_date.year



    @api.onchange('start_date', 'end_date')
    def _onchange_dates_set_name(self):
        """Automatically generate name and code when dates are updated."""
        if self.start_date and self.end_date:
            start_year = self.start_date.year
            end_year = self.end_date.year
            self.name = f"{start_year}-{end_year}"

    @api.constrains('name')
    def _check_unique(self):
        for record in self:
            if self.search([('id', '!=', record.id), ('name', '=', record.name)]):
                raise ValidationError(f"Academic Year  '{record.name}' already exists.")

