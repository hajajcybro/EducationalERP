# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

class EducationEnrollment(models.Model):
    _name = 'education.enrollment'
    _description = 'Student Enrollment'
    _inherit = ['mail.thread']
    _rec_name = 'student_id'
    _order = 'enrollment_date desc'

    student_id = fields.Many2one(
        'education.student.student',
        string='Student',
        required=True,
        ondelete='cascade',
        help='Student being enrolled.'
    )
    current_class_id =fields.Many2one('education.class',string='Class',
                                      required=True,
                                      )
    academic_year_id = fields.Many2one(
        'education.academic.year',
        string='Academic Year',
        compute='_compute_academic_year',
        store=True,
     )
    enrollment_date = fields.Date(
        string='Enrollment Date',
        default=fields.Date.context_today,
        readonly=True,
    )
    start_date = fields.Date(string='Start Date')
    end_date = fields.Date(string='End Date')
    status = fields.Selection([
        ('draft', 'Draft'),
        ('enrolled', 'Enrolled'),
        ('promoted', 'Promoted'),
        ('retained', 'Retained'),
        ('dropped', 'Dropped'),
        ('completed', 'Completed')
        ], string='Status', default='draft', tracking=True
    )
    fee_plan_id = fields.Char(string='Fee Plan')
    roll_number = fields.Integer(
        string='Roll Number',
        store=True,
        compute='_compute_roll_number',
        help='Automatically assigned roll number per class and academic year.'
    )
    remarks = fields.Text(string='Remarks')
    student_image = fields.Image(
        string='Student Image',
        related='student_id.photo',
        readonly=True
    )

    _sql_constraints = [
        ('unique_enrollment',
         'unique(student_id,current_class_id)',
         'A student cannot be enrolled multiple times.')
    ]

    def action_enroll(self):
        """Mark as enrolled and update student's state."""
        for rec in self:
            rec.status = 'enrolled'
            if rec.student_id:
                rec.student_id.state = 'enrolled'

    @api.depends('current_class_id')
    def _compute_academic_year(self):
        """Automatically set academic year based on the selected class."""
        for rec in self:
            if rec.current_class_id:
                rec.academic_year_id = rec.current_class_id.academic_year_id
            else:
                rec.academic_year_id = False

    @api.depends('current_class_id', 'academic_year_id')
    def _compute_roll_number(self):
        """Assign roll numbers sequentially per class and academic year."""
        for rec in self:
            if rec.current_class_id and rec.academic_year_id:
                # Find the maximum roll number in the class + year
                last_roll = self.search(
                    [
                        ('current_class_id', '=', rec.current_class_id.id),
                        ('academic_year_id', '=', rec.academic_year_id.id)
                    ], order='roll_number desc', limit=1).roll_number
                rec.roll_number = (last_roll or 0) + 1


    @api.model_create_multi
    def create(self, vals_list):
        """Create enrollment and update linked student's state and current enrollment."""
        records = super().create(vals_list)
        for rec in records:
            if rec.student_id:
                rec.student_id.write({
                    'state': 'enrolled',
                    'current_enrollment_id': rec.id,
                })
        return records

