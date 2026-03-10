from odoo import api, fields, models

class EducationExamSupplementary(models.Model):
    _name = 'education.exam.supplementary'
    _description = 'Supplementary Exam Application'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Order Reference', required=True, copy=False, readonly=True,
                       default=lambda self: ('New'))
    student_id = fields.Many2one('res.partner', string='Student/Alumni', required=True,
                                 domain=[('position_role', 'in', ['student', 'alumni'])])
    exam_id = fields.Many2one('education.exam', string='Exam', required=True)
    course_id = fields.Many2one('education.subject', string='Course', required=True)
    program_id = fields.Many2one('education.program', string='Program')
    session_id = fields.Many2one('education.session', string="Session")

    @api.model_create_multi
    def create(self, vals_list):
        """Generate sequence reference"""
        for vals in vals_list:
            if vals.get('name', ('New')) == ('New'):
                # You can create an ir.sequence for this later, or just let it use 'New' for now
                vals['name'] = self.env['ir.sequence'].next_by_code('education.exam.supplementary') or ('New')
        return super().create(vals_list)

    def action_confirm(self):
        self.state = 'confirm'

    def action_cancel(self):
        self.state = 'cancel'