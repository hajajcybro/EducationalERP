from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class EducationExamResultLine(models.Model):
    """
        Model used to show marks in each subjects.
        """
    _name = 'education.exam.result.line'
    _description = 'Education Exam Result Line'

    name = fields.Char(string='Name',
                       help='Name associated with the subject result entry.')
    course_id = fields.Many2one('education.subject',
                                 string='Course',
                                 help='Course associated with the result.')
    max_mark = fields.Float(string='Max Mark',
                            help='Maximum mark of Course.')
    pass_mark = fields.Float(string='Pass Mark',
                             help='Pass mark of Course.')
    new_mark = fields.Float(string='Revaluation Mark',
                             help='Revaluation mark of Course.')
    mark_scored = fields.Float(string='Mark Scored',
                               help='Marks obtained by the student in the '
                                    'Course.')
    pass_or_fail = fields.Boolean(string='Pass/Fail',
                                  help='Pass or fail status for the '
                                       'Course result.')
    result_id = fields.Many2one('education.exam.result',
                                string='Exam Result',
                                help='Reference to the exam result.')
    exam_id = fields.Many2one('education.exam', string='Exam',
                              help='Reference of the exam.')
    grade_id = fields.Many2one('education.exam.grade', string='Grade', )

