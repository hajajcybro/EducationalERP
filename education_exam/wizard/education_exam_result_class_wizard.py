from odoo import api, fields, models

class ExamResultClassReportWizard(models.TransientModel):
    _name = 'exam.result.class.report.wizard'
    _description = 'Class-wise Exam Result Report Wizard'

    class_id = fields.Many2one('education.class', string='Class', required=True)
    exam_id = fields.Many2one('education.exam', string='Exam', required=True)
    session_id = fields.Many2one('education.session', string='Session')

    def print_report(self):
        print("helooooooooooooo")
        return self.env.ref('education_exam.action_report_classwise_exam_result_pdf').report_action(self)

