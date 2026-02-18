from odoo import api, fields, models,_


class EducationExamResults(models.Model):
    """
        Model used for create and manage  Exam Results.
        """
    _name = 'education.exam.result'
    _description = 'Exam Results'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Name',
                       help='Sequence of Exam result.')
    program_id = fields.Many2one('education.program', string="Program")
    class_id = fields.Many2one('education.class', string="Class")
    session_id = fields.Many2one('education.session', string="Session",
                                 domain="[('program_id', '=', program_id)]")
    academic_year_id = fields.Many2one('education.academic.year', string='Academic Year',
                                       related='session_id.academic_year_id', required=True)

    exam_id = fields.Many2one('education.exam', string='Exam',
                              help='Select the exam associated with the result.')
    exam_type_id = fields.Many2one('education.exam.type', string='Exam Type')

    student_id = fields.Many2one('res.partner', string='Student',
                                 help='Name of the student')
    total_mark_scored = fields.Float(string='Total Marks Scored', store=True,
                                     readonly=True, compute='_compute_total_mark_scored',
                                     help='Total marks scored by the student.')
    all_pass = fields.Boolean(string='Overall Pass/Fail', store=True,
                                  readonly=True, compute='_compute_total_mark_scored',
                                  help='Overall Pass/Fail status of the student.')
    total_max_mark = fields.Float(string='Total Mark', store=True,
                                  readonly=True, compute='_compute_total_mark_scored',
                                  help='Total maximum marks for the exam.')
    result_line_ids = fields.One2many('education.exam.result.line',
                                       'result_id',
                                       string='Courses',
                                       help='Courses in examination')
    overall_grade =fields.Many2one('education.exam.grade',string='Overall Grade',)
    valuation_completed = fields.Boolean(string='Valuation Completed',defauilt=False,copy=False)



    @api.depends('result_line_ids.mark_scored','result_line_ids.new_mark')
    def _compute_total_mark_scored(self):
        print("total_mark_scored")
        for rec in self:
            total_pass_mark = 0
            total_max_mark = 0
            total_mark_scored = 0
            overall_pass = True
            print("11111111111111111111111111",rec.result_line_ids)
            for subjects in rec.result_line_ids:
                print("2222222222222222222",subjects.mark_scored)
                total_pass_mark += subjects.pass_mark
                total_max_mark += subjects.max_mark
                if subjects.new_mark:
                    total_mark_scored += subjects.new_mark
                else:
                    total_mark_scored += subjects.mark_scored
                if not subjects.pass_or_fail:
                    overall_pass = False
            # rec.total_pass_mark = total_pass_mark
            rec.total_max_mark = total_max_mark
            rec.total_mark_scored = total_mark_scored
            mark_percentage = (total_mark_scored / total_max_mark)
            print("mark_percentage:", mark_percentage)
            grade = self.env['education.exam.grade'].search([
                ('percentage_from', '<=', mark_percentage),
                ('percentage_to', '>=', mark_percentage)
            ])

            rec.overall_grade = grade.id
            rec.all_pass = overall_pass

    @api.model_create_multi
    def create(self, vals_list):
        """override create method for reference generation"""
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('education.exam.result') or _('New')
        return super().create(vals_list)
