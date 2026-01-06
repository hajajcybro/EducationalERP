# -*- coding: utf-8 -*-

from odoo import models, fields, api,_
from odoo.exceptions import ValidationError

class EducationClass(models.Model):
    _name = 'education.class'
    _description = 'Education Class'
    _inherit  = ['mail.thread', 'mail.activity.mixin']
    _order = 'name'

    name = fields.Char(string='Class Name',required=True,
                       help='Enter the name of the class')
    program_id = fields.Many2one('education.program', string='Education Program',required=True,
                    help='Specify the education program or course this class belongs to'
                             )
    academic_year_id = fields.Many2one('education.academic.year',string='Academic Year', required=True,
                    help = 'Select the academic year during which this class will run'
                                   )
    capacity = fields.Integer(string='Room Capacity',  compute='_compute_capacity',
                              help='Maximum number of students that can be enrolled in this class'
                              )
    class_teacher_id = fields.Many2one('hr.employee', string='Class Teacher', domain=[('role', '=', 'teacher')],
                        help = 'Assign a teacher who will be responsible for this class.',required=True,
    )
    room_id = fields.Many2one('education.class.room',string='Room No', required=True,
                          help='Specify the room or hall number where this class will be conducted.'
                          )
    notes = fields.Text(string='Notes',
                        help='Additional notes or information about this class.'
                        )
    active = fields.Boolean(string='Active',
        default=True,
        help='Uncheck to archive this class and hide it from selection lists.'
    )
    student_ids = fields.One2many('res.partner','class_id')
    session_id = fields.Many2one('education.session',string='Session')
    timetable_line_ids = fields.One2many('education.timetable.line','class_id')
    program_type = fields.Selection(
        [('school', 'School'), ('college', 'College')],
        string='Program Type', readonly=True
    )
    division = fields.Char(
        string='Division',
        help='Class division (A, B, C, etc.)'
    )

    @api.onchange('program_id')
    def _onchange_program_id(self):
        """Update the program type automatically when the program is changed."""
        if self.program_id:
            self.program_type = self.program_id.education_type

    @api.depends('room_id')
    def _compute_capacity(self):
        """Compute the class capacity based on the selected room."""
        for rec in self:
            rec.capacity = rec.room_id.capacity if rec.room_id else 0

    @api.constrains('room_id', 'academic_year_id')
    def _check_duplicate_room_assignment(self):
        """Prevent assigning the same room to multiple classes
            in the same academic year."""
        for rec in self:
            if rec.room_id and rec.academic_year_id:
                existing = self.search([
                    ('id', '!=', rec.id),
                    ('room_id', '=', rec.room_id.id),
                    ('academic_year_id', '=', rec.academic_year_id.id)
                ], limit=1)
                if existing:
                    raise ValidationError('already assigned')

    @api.constrains('program_id', 'academic_year_id')
    def _check_program_year_duration(self):
        """ Ensure the Academic Year duration matches the selected Program's duration.
        Raises a ValidationError if both durations are different."""
        for rec in self:
            if rec.program_id and rec.academic_year_id:
                if int(rec.academic_year_id.duration) != rec.program_id.duration:
                    raise ValidationError("Program duration must match academic year duration.")

    @api.constrains('room_id')
    def _check_room_already_allocated(self):
        """Prevent assigning the same room to multiple classes."""
        for rec in self:
            if rec.room_id and self.search_count([
                ('id', '!=', rec.id),
                ('room_id', '=', rec.room_id.id),
            ]):
                raise ValidationError(_("Room is already assigned to another class."))


