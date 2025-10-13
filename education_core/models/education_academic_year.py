# -*- coding: utf-8 -*-
from odoo import api, fields, models,_
from odoo.exceptions import ValidationError


class EducationAcademicYear(models.Model):
    """ This model represents education.academic.year."""
    _name = 'education.academic.year'
    _description = 'EducationAcademicYear'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'
    _order = 'start_date desc'

    name = fields.Char(string='Academic Year', required=True, unique=True)
    code = fields.Char(string='Code', help='Short code for Academic Year, e.g., AY25-26')
    start_date = fields.Date(string='Start Date', required=True)
    end_date = fields.Date(string='End Date', required=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('closed', 'Closed')
    ], string='Status', default='draft')
    is_current = fields.Boolean(string='Current Year', default=False,
                                help='Marks the current academic year.')
    active = fields.Boolean(string='Active', default=True)
    notes = fields.Text(string='Notes')

    # Relations
    session_ids = fields.One2many(
        comodel_name='education.session',  # The model this links to
        inverse_name='academic_year_id',  # The Many2one field in session
        string='Sessions'
    )
    class_ids = fields.Char(string='Classes')
    program_ids = fields.Char(string='Programs')

    _sql_constraints = [
        ('name_unique', 'unique(name)', 'The Academic Year name must be unique.'),
        # ('code_unique', 'unique(code)', 'The Academic Year code must be unique.')
    ]

    @api.constrains('start_date', 'end_date')
    def _check_dates(self):
        for record in self:
            if record.start_date > record.end_date:
                raise ValidationError("Start date must be before end date.")

    @api.onchange('is_current')
    def _onchange_is_current(self):
        if self.is_current:
            # Ensure only one academic year is current
            other_years = self.search([('id', '!=', self.id), ('is_current', '=', True)])
            for year in other_years:
                year.is_current = False

    @api.constrains('name')
    def _check_unique(self):
        for record in self:
            if self.search([('id', '!=', record.id), ('name', '=', record.name)]):
                raise ValidationError(f"Academic Year with name '{record.name}' already exists.")

    def unlink(self):
        """Return validation error on deleting the academic year"""
        for rec in self:
            raise ValidationError(
                _("Academic Year can not be deleted, You only can "
                  "Archive it."))
