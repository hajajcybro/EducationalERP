from odoo import api, fields, models,_
from odoo.exceptions import UserError, ValidationError


class EducationExamREValuation(models.Model):

    _name = 'education.exam.revaluation'
    _description = 'Education Exam ReValuation'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    name = fields.Char(
        string="Order Reference",
        required=True, copy=False, readonly=False,
        index='trigram',
        default=lambda self: _('New'))

    exam_id = fields.Many2one('education.exam',string='Exam',required=True)
    revaluation_id = fields.Many2one('education.exam.revaluation.creation',string='Exam Revaluation Creation')
    class_id = fields.Many2one('education.class',string='Class')
    student_id = fields.Many2one('res.partner',string='Student', domain=[('position_role', '=', 'student')])
    # # division_id = fields.Many2one('education.division',string='Division')
    program_id = fields.Many2one('education.program',string='Program')
    session_id = fields.Many2one('education.session', string="Session")
    course_id = fields.Many2one('education.subject',string='Course',required=True)
    date = fields.Date(string='Date' ,default=fields.Date.context_today)
    employee_id = fields.Many2one('hr.employee',string='Teacher')
    state = fields.Selection(
        [('draft', 'Draft'), ('confirm', 'Confirm'),
         ('cancel', 'Canceled')], default='draft', help='State of the Exam Revaluation Request.')
    is_mark_sheet_created = fields.Boolean(
        string='Mark sheet Created', copy=False,
        help='Flag indicating whether the mark sheet is created or not.')

    # revaluation_line_ids = fields.One2many(
    #     'education.exam.valuation.line',
    #     'valuation_id', string='Students',
    #     help='Students details in the valuation.')
    def action_confirm(self):
        self.state = 'confirm'
    def action_cancel(self):
        self.state = 'cancel'

    @api.onchange('exam_id')
    def _onchange_exam_id(self):
        """
         Used to raise an error when pass mark greater than max mark
        """
        print("888888888888888")
        if self.exam_id:
            if self.exam_id.program_id:
                self.program_id = self.exam_id.program_id
                self.session_id = self.exam_id.session_id
            if self.exam_id.class_id:
                self.class_id = self.exam_id.class_id


        domain = []
        courses = self.exam_id.course_line_ids
        for rec in courses:
            domain.append(rec.course_id.id)
        return {'domain': {'course_id': [('id', 'in', domain)]}}

    @api.onchange('date')
    def _onchange_date(self):
        print("88888888888888")


    @api.model_create_multi
    def create(self, vals_list):
        """override create method for reference generation"""

        for vals in vals_list:
            print("1111111111111111", vals)

            # revaluation_id = self.env['education.exam.revaluation.creation'].search([('exam_id', '=', vals['exam_id'])],
            #                                                                         limit=1)
            # print(";;;;;;;;;;;;;;;;;;", revaluation_id,self.revaluation_id.start_date,self.revaluation_id.end_date)
            # if self.revaluation_id.start_date <= self.date <= self.revaluation_id.end_date:
            #     print("jjjjjjjjjjjjjjj")
            #     raise ValidationError(
            #         _("Start date must be less than end date"))

            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('education.exam.revaluation') or _('New')
        return super().create(vals_list)


