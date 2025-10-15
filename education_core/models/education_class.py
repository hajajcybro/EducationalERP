# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError

class EducationClass(models.Model):
    _name = 'education.class'
    _description = 'Education Class'
    _inherit  = 'mail.thread'
    _rec_name = 'name'
    _order = 'name'

    name = fields.Char(string='Class Name',required=True,
                       help='Enter the name of the class')
    program_id = fields.Many2one('education.program', string='Education Program',
                    help='Specify the education program or course this class belongs to'
                             )
    academic_year_id = fields.Many2one('education.academic.year',string='Academic Year', required=True,
                    help = 'Select the academic year during which this class will run'
                                   )
    capacity = fields.Integer(string='Room Capacity',  compute='_compute_capacity', readonly=True,
                              help='Maximum number of students that can be enrolled in this class'
                              )
    class_teacher_id = fields.Many2one('res.partner', string='Class Teacher', required=True,
                        help = 'Assign a teacher who will be responsible for this class.'
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




    @api.depends('room_id')
    def _compute_capacity(self):
        for rec in self:
            rec.capacity = rec.room_id.capacity if rec.room_id else 0
