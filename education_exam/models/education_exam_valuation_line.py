from odoo import api, fields, models,_
from odoo.exceptions import UserError, ValidationError

class EducationExamValuationLine(models.Model):
    """
        Model representing the students in exam valuation.
        """
    _name = 'education.exam.valuation.line'
    _description = 'Exam Valuation Line'

    student_id = fields.Many2one('res.partner', string='Student',
                                 help='Student associated with '
                                      ' valuation line.')
    mark_scored = fields.Float(string='Mark Scored',
                               help='Marks obtained by the student in the exam.')
    new_mark = fields.Float(string='New Mark',
                            help='Revaluation mark of Course.')
    pass_or_fail = fields.Boolean(string='Pass/Fail',
                                  help='Boolean used to identify whether the student is pass or fail.')
    valuation_id = fields.Many2one('education.exam.valuation',
                                   string='Valuation',
                                   help='Connection filed to exam valuation.')

    @api.onchange('mark_scored', 'pass_or_fail','new_mark')
    def _onchange_mark_scored(self):
        """
            Onchange method to update the student is pass_or_fail.
        """
        if self.mark_scored > self.valuation_id.max_mark:
            raise UserError(_('Obtained Mark must be less than Maximum  Mark'))
        if self.new_mark > self.valuation_id.max_mark:
            raise UserError(_('Obtained Mark must be less than Maximum  Mark'))
        if self.new_mark >= self.valuation_id.pass_mark:
            self.pass_or_fail = True
        elif self.mark_scored >= self.valuation_id.pass_mark:
            self.pass_or_fail = True
        else:
            self.pass_or_fail = False


    def write(self, vals):
        res = super().write(vals)
        result_line =[]
        if 'new_mark' in vals:
            exam_result_line_obj = self.env['education.exam.result.line']
            for line in self:
                # Find the corresponding exam result line
                result_line = exam_result_line_obj.search([
                    ('result_id.exam_id', '=', line.valuation_id.exam_id.id),
                    ('result_id.class_id', '=', line.valuation_id.class_id.id),
                    ('course_id', '=', line.valuation_id.course_id.id),
                    ('result_id.student_id', '=', line.student_id.id)
                ], limit=1)

        if result_line:
            result_line.write({
                'new_mark': line.new_mark,
                'pass_or_fail': line.pass_or_fail,
            })
        return res