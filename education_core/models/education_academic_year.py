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
    duration = fields.Char(string='Duration', compute='_compute_dates', store=True,
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
    # Closure Summary (populated when year is closed)
    total_converted = fields.Integer(
        string='Total Converted to Alumni',
        readonly=True,
        help='Number of students converted to Alumni on year close.'
    )
    total_skipped = fields.Integer(
        string='Total Skipped (Dropped)',
        readonly=True,
        help='Number of dropped students skipped during Alumni conversion.'
    )
    closed_on = fields.Date(
        string='Closed On',
        readonly=True,
        help='Date on which this academic year was closed.'
    )

    @api.depends('start_date', 'end_date')
    def _compute_dates(self):
        """   Compute duration from start and end dates.
            Validates that start date is not after end date.
            Duration is calculated as end year minus start year."""
        for rec in self:
            rec.duration = 0
            if rec.start_date and rec.end_date:
                if rec.start_date > rec.end_date:
                    raise ValidationError(
                        "Start date must be before end date."
                    )
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

    def action_set_active(self):
        for rec in self:
            rec.state = 'active'

    # def action_set_closed(self):
    #     for rec in self:
    #         rec.state = 'closed'

    def action_set_closed(self):
        """
        Close the academic year and convert all non-dropped students to Alumni.
        Flow:
          1. Find all students (res.partner) linked to this academic year.
          2. Separate dropped students (skip) from the rest (convert).
          3. For each convertible student:
               - Generate Alumni ID from sequence.
               - Determine alumni_status based on enrollment status.
               - Write alumni fields onto res.partner.
               - Change position_role → 'alumni'.
               - Mark enrollment → 'completed'.
               - Send welcome notification.
          4. Write closure summary fields.
          5. Set state → 'closed'.
          6. Create audit log entry.
        """
        for rec in self:
            # Find all students in this academic year
            all_students = self.env['res.partner'].search([
                ('academic_year_id', '=', rec.id),
                ('position_role', '=', 'student'),
            ])
            dropped_partners = self.env['education.enrollment'].search([
                ('academic_year_id', '=', rec.id),
                ('status', '=', 'dropped'),
            ]).mapped('student_id.partner_id')
            convertible = all_students.filtered(
                lambda s: s not in dropped_partners
            )
            dropped = all_students.filtered(
                lambda s: s in dropped_partners
            )
            graduation_year = str(rec.end_date.year)
            converted_count = 0
            # Convert each student → Alumni
            for student in convertible:
                enrollment = student.current_enrollment_id
                alumni_status = 'graduated'
                # Generate unique Alumni ID  (sequence: ALM/2023/0001)
                alumni_reference = self.env['ir.sequence'].next_by_code(
                    'alumni.id.sequence'
                ) or '/'
                student.write({
                    'position_role': 'alumni',
                    'alumni_reference': alumni_reference,
                    'alumni_status': alumni_status,
                    'graduation_year': graduation_year,
                })
                if enrollment:
                    enrollment.write({'status': 'completed'})
                converted_count += 1
            rec.write({
                'state': 'closed',
                'is_current': False,
                'total_converted': converted_count,
                'total_skipped': len(dropped),
                'closed_on': fields.Date.today(),
            })
            