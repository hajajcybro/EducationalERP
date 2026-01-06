# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

class EducationEnrollment(models.Model):
    _name = 'education.enrollment'
    _description = 'Student Enrollment'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'student_id'
    _order = 'enrollment_date desc'

    student_id = fields.Many2one(
        'education.application',
        string='Student',
        required=True,
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
        ('completed', 'Completed'),
        ('dropped', 'Dropped'),
        ], string='Status', default='draft', tracking=True
    )
    roll_number = fields.Integer(
        string='Roll Number',
        store=True,
        help='Automatically assigned roll number per class and academic year.')
    remarks = fields.Text(string='Remarks')

    def action_enroll(self):
        """Mark as enrolled"""
        for rec in self:
            rec.status = 'enrolled'

    def action_dropped(self):
        """Mark as dropped"""
        for rec in self:
            rec.status = 'dropped'

    def _assign_roll_number(self):
        """Assign the next available roll number for the class and academic year."""
        for rec in self:
            if not rec.current_class_id or not rec.academic_year_id:
                continue
            last_student = self.env['res.partner'].search([
                ('is_student', '=', True),
                ('class_id', '=', rec.current_class_id.id),
                ('academic_year_id', '=', rec.academic_year_id.id),
                ('roll_no', '!=', False),
            ], order="roll_no desc", limit=1)
            last_roll = int(last_student.roll_no) if last_student else 0
            rec.roll_number = last_roll + 1

    @api.model_create_multi
    def create(self, vals_list):
        """Create enrollment, assign roll number, and update student records."""
        records = super().create(vals_list)
        for rec in records:
            if not rec.roll_number:
                rec._assign_roll_number()
                rec.write({'roll_number': rec.roll_number
                })
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
                partner = rec.student_id.partner_id
                if partner:
                    partner.write({
                        'class_id': rec.current_class_id.id,
                        'roll_no': rec.roll_number,
                        'class_teacher_id': rec.teacher_id.id,
                    })
        return records\



