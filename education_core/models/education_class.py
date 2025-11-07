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
    student_ids = fields.One2many('education.enrollment','current_class_id')
    session_id = fields.Many2one('education.session',string='Session')
    timetable_line_ids = fields.One2many('education.timetable.line','class_id')
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
                    raise ValidationError((
                        f"Room '{rec.room_id.name}' is already assigned to class "
                        f"'{existing.name}' for academic year '{rec.academic_year_id.name}'."
                    ))

    @api.constrains('program_id', 'academic_year_id')
    def _check_program_year_duration(self):
        for rec in self:
            if rec.program_id and rec.academic_year_id:
                if int(rec.academic_year_id.duration) != rec.program_id.duration:
                    raise ValidationError(
                        f"Academic year '{rec.academic_year_id.name}' (duration {rec.academic_year_id.duration}) "
                        f"does not match the duration of program '{rec.program_id.name}' ({rec.program_id.duration} years)."
                    )

    @api.constrains('student_ids', 'capacity')
    def _check_capacity_not_exceeded(self):
        """Prevent enrollment beyond room capacity."""
        for rec in self:
            enrolled = len(rec.student_ids.filtered(lambda s: s.status == 'enrolled'))
            if enrolled > rec.capacity:
                raise ValidationError(_(
                    "Class capacity exceeded!\n"
                    "Current enrollments: %d\n"
                    "Maximum capacity: %d\n"
                    "Please increase room capacity or move students to another class."
                ) % (enrolled, rec.capacity))