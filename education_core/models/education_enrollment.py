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
        'education.application',
        string='Student',
        required=True,
        ondelete='cascade',
        help='Student being enrolled.'
    )
    admission_no = fields.Char(related='student_id.admission_no', string="Register No")
    email = fields.Char(related='student_id.email', string="Email")
    student_image = fields.Image(
        string='Student Image',
        related='student_id.photo',
        readonly=True
    )
    academic_year_id = fields.Many2one('education.academic.year',related='student_id.academic_year_id',
        string='Academic Year',
     )
    program_id = fields.Many2one('education.program',related='student_id.program_id',
        string='Program',
     )
    current_class_id =fields.Many2one(
        'education.class',string='Class',
        required=True,
    )


    teacher_id = fields.Many2one(related='current_class_id.class_teacher_id',
        string='Class Teacher',
     )
    enrollment_date = fields.Date(
        string='Enrollment Date',
        default=fields.Date.context_today,
        readonly=True,
    )
    status = fields.Selection([
        ('draft', 'Draft'),
        ('enrolled', 'Enrolled'),
        ('promoted', 'Promoted'),
        ('retained', 'Retained'),
        ('dropped', 'Dropped'),
        ('completed', 'Completed')
        ], string='Status', default='draft', tracking=True
    )
    roll_number = fields.Integer(
        string='Roll Number',
        store=True,

        help='Automatically assigned roll number per class and academic year.'
    )
    remarks = fields.Text(string='Remarks')


    _sql_constraints = [
        ('unique_enrollment',
         'unique(student_id,current_class_id,academic_year_id)',
         'A student cannot be enrolled multiple times.')
    ]

    def action_enroll(self):
        """Mark as enrolled and update student's state."""
        for rec in self:
            rec.status = 'enrolled'
            if rec.student_id:
                rec.student_id.state = 'enrolled'

                # Update res.partner with class and roll details
                student = rec.student_id
                if student.partner_id:
                    student.partner_id.write({
                        'class_id': rec.current_class_id.id,
                        'academic_year_id': rec.academic_year_id.id,
                        'program_id': rec.program_id.id,
                        'roll_no': rec.roll_number,
                    })

    def _assign_roll_number(self):
        """Assign sequential roll number based on class and academic year."""
        for rec in self:
            if not rec.current_class_id or not rec.academic_year_id:
                continue

            last_enrollment = self.search([
                ('current_class_id', '=', rec.current_class_id.id),
                ('academic_year_id', '=', rec.academic_year_id.id),
            ], order='roll_number desc', limit=1)

            rec.roll_number = (last_enrollment or 0) + 1

    # @api.depends('current_class_id', 'academic_year_id')
    # def _compute_roll_number(self):
    #     """Assign roll numbers sequentially per class and academic year."""
    #     for rec in self:
    #         if rec.current_class_id and rec.academic_year_id:
    #             # Find the maximum roll number in the class + year
    #             last_roll = self.search(
    #                 [
    #                     ('current_class_id', '=', rec.current_class_id.id),
    #                     ('academic_year_id', '=', rec.academic_year_id.id)
    #                 ], order='roll_number desc', limit=1).roll_number
    #             rec.roll_number = (last_roll or 0) + 1


    @api.model_create_multi
    def create(self, vals_list):
        """Create enrollment and update linked student's state and current enrollment."""
        records = super().create(vals_list)
        for rec in records:
            existing = self.search([
                ('student_id', '=', rec.student_id.id),
                ('status', '=', 'enrolled'),
                ('id', '!=', rec.id)
            ], limit=1)
            if existing:
                raise ValidationError(_(
                    "Student '%s' is already enrolled in another class (%s)."
                ) % (rec.student_id.name, existing.current_class_id.display_name))

            if rec.student_id:
                rec.student_id.write({
                    'state': 'enrolled',
                    'current_enrollment_id': rec.id,
                })
        return records

