from odoo import api, fields, models,_
from odoo.exceptions import UserError, ValidationError


class EducationExamValuation(models.Model):

    _name = 'education.exam.valuation'
    _description = 'Education Exam Valuation'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    name = fields.Char(
        string='Name', default='New', help='Name of the education exam.')
    exam_id = fields.Many2one('education.exam',string='Exam')
    class_id = fields.Many2one('education.class',string='Class')
    # division_id = fields.Many2one('education.division',string='Division')
    program_id = fields.Many2one('education.program',string='Program')
    session_id = fields.Many2one('education.session', string="Session")
    course_id = fields.Many2one('education.subject',string='Course',required=True,domain="[('program_id', '=', program_id)]")
    # date = fields.Datetime(string='Valuation Date')
    employee_id = fields.Many2one('hr.employee',string='Teacher')
    max_mark = fields.Float(string='Maximum Mark')
    pass_mark = fields.Float(string='Pass Mark')
    state = fields.Selection(
        [('draft', 'Draft'), ('published', 'Published'),
         ('cancel', 'Canceled')], default='draft', help='State of the exam valuation.')
    is_mark_sheet_created = fields.Boolean(
        string='Mark sheet Created', copy=False,
        help='Flag indicating whether the mark sheet is created or not.')

    valuation_line_ids = fields.One2many(
        'education.exam.valuation.line',
        'valuation_id', string='Students',
        help='Students details in the valuation.')

    @api.onchange('pass_mark')
    def _onchange_pass_mark(self):
        """
         Used to raise an error when pass mark greater than max mark
        """
        if self.pass_mark > self.max_mark:
            raise UserError(_('Pass mark must be less than Max Mark'))

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
            if self.course_id:
                for course in self.exam_id.course_line_ids:
                    print("heloooooooooooooooooooooooooooooo")
                    if course.course_id.id == self.course_id.id:
                        if course.max_marks:
                            self.max_mark = course.max_marks
        domain = []
        courses = self.exam_id.course_line_ids
        for rec in courses:
            domain.append(rec.course_id.id)
        return {'domain': {'course_id': [('id', 'in', domain)]}}

    def action_cancel(self):
        """
            Set the exam valuation state to 'cancel'.
        """
        self.state = 'cancel'

    def action_complete(self):
        """
           The function used create exam result after the valuation
        """
        exam_result_obj = self.env['education.exam.result']
        exam_result_line_obj = self.env['education.exam.result.line']
        for students in self.valuation_line_ids:
            search_result = exam_result_obj.search(
                [('exam_id', '=', self.exam_id.id),
                 ('class_id', '=', self.class_id.id),
                 ('student_id', '=', students.student_id.id)])
            print("search_result",students)
            mark_percentage = 0.0
            if self.max_mark:
                mark_percentage = (students.mark_scored / self.max_mark)
                print("mark_percentage:", mark_percentage)
                grade = self.env['education.exam.grade'].search([
                    ('percentage_from', '<=', mark_percentage),
                    ('percentage_to', '>=', mark_percentage)
                ])

            if len(search_result) < 1:
                result_data = {
                    # 'name': self.name,
                    'exam_id': self.exam_id.id,
                    'class_id': self.class_id.id,
                    'program_id': self.program_id.id if self.program_id else '' ,
                    'session_id': self.session_id.id if self.session_id else '',
                    'student_id': students.student_id.id,
                }
                result = exam_result_obj.create(result_data)
                result_line_data = {
                    # 'name': self.name,
                    'course_id': self.course_id.id,
                    'max_mark': self.max_mark,
                    'pass_mark': self.pass_mark,
                    'mark_scored': students.mark_scored,
                    'pass_or_fail': students.pass_or_fail,
                    'grade_id': grade.id,
                    'result_id': result.id,
                }
                exam_result_line_obj.create(result_line_data)
            else:
                result_line_data = {
                    'course_id': self.course_id.id,
                    'max_mark': self.max_mark,
                    'pass_mark': self.pass_mark,
                    'mark_scored': students.mark_scored,
                    'pass_or_fail': students.pass_or_fail,
                    'result_id': search_result.id,
                    'grade_id': grade.id,
                }
                exam_result_line_obj.create(result_line_data)
        self.state = 'published'



    def action_create_mark_sheet(self):
        """
            Create Mark sheet for the exam valuation.
            """
        print("Creating Mark sheet")
        valuation_line_obj = self.env['education.exam.valuation.line']
        if self.program_id:
            student_ids = self.env['res.partner'].search([('program_id', '=', self.program_id),('position_role','=','student')])
        print("oooooooooooo",student_ids)
        if self.exam_id:
            student_ids = self.env['res.partner'].search([('class_id', '=', self.class_id)])
        if len(student_ids) < 1:
            raise UserError(_('There are no students'))
        for student in student_ids:
            data = {
                'student_id': student.id,
                'valuation_id': self.id,
            }
            valuation_line_obj.create(data)
        self.is_mark_sheet_created = True
        print("self.is_mark_sheet_created",self.is_mark_sheet_created)

    @api.model_create_multi
    def create(self, vals_list):
        """Override create method to generate name based on given details"""
        records = super().create(vals_list)
        for rec in records:
            parts = []

            # Program / Session / Class
            if rec.program_id:
                parts.append(rec.program_id.name)
                if rec.session_id:
                    parts.append(rec.session_id.name)

            if rec.class_id:
                if rec.program_id:
                    parts.append(rec.class_id.name)
                else:
                    parts = [rec.class_id.name]

            # Exam details
            if rec.exam_id and rec.exam_id.start_date and rec.exam_id.end_date:
                exam_type = rec.exam_id.exam_type_id.name
                start = rec.exam_id.start_date.strftime('%d-%m-%Y')
                end = rec.exam_id.end_date.strftime('%d-%m-%Y')
                parts.append(f"{exam_type}-{start} To {end}")

            rec.name = "-".join(parts)

        return records








