from odoo import models, api


class EducationExamNotification(models.Model):
    """
    Inherits education.exam to send portal notifications when:
    1. Admin publishes a new exam  (state -> 'published')
    2. Admin publishes exam results (state -> 'result')
    """
    _inherit = 'education.exam'

    class EducationExamNotification(models.Model):
        """
        Inherits education.exam to send portal notifications when:
        1. Admin confirms/publishes a new exam   (action_confirm → state = 'published')
        2. Cron publishes exam results           (valuation_completed = True)
        """
        _inherit = 'education.exam'

        def write(self, vals):
            res = super().write(vals)

            if 'state' in vals and vals['state'] == 'published':
                for rec in self:
                    # Students are res.partner directly (position_role = 'student')
                    students = self.env['res.partner'].search([
                        ('class_id', '=', rec.class_id.id),
                        ('position_role', '=', 'student')
                    ])
                    recipient_ids = [(4, s.id) for s in students]
                    if recipient_ids:
                        notif = self.env['edu.notification'].sudo().create({
                            'name': f'New Exam Published: {rec.name}',
                            'message': f'A new exam "{rec.name}" has been published. Please check the Exams section for details.',
                            'recipient_ids': recipient_ids,
                            'module': 'exam',
                            'notification_type': 'in_app',
                            'status': 'draft',
                        })
                        notif.action_send()
            return res

    class EducationExamValuationNotification(models.Model):
        """
        Inherits education.exam.valuation to send portal notifications
        when results are published (action_complete sets state = 'published').
        Each student in valuation_line_ids gets their own personal message.
        """
        _inherit = 'education.exam.valuation'

        def action_complete(self):
            """
            Override action_complete to send notifications AFTER
            the parent method creates results and sets state = 'published'.
            """
            res = super().action_complete()
            # At this point state is 'published', notify each student
            for line in self.valuation_line_ids:
                student = line.student_id  # res.partner directly
                if not student:
                    continue
                result_text = 'Pass' if line.pass_or_fail == 'pass' else 'Fail'
                notif = self.env['edu.notification'].sudo().create({
                    'name': f'Exam Result Published: {self.exam_id.name}',
                    'message': (
                        f'Your result for "{self.exam_id.name}" - '
                        f'has been published. '
                        f'Please check the Exam Results section.'
                    ),
                    'recipient_ids': [(4, student.id)],
                    'module': 'exam',
                    'notification_type': 'in_app',
                    'status': 'draft',
                })
                notif.action_send()

            return res












