from odoo import models, fields, api


class EducationScholarshipNotification(models.Model):
    """
    Inherits education.scholarship to send portal notifications
    when admin opens a scholarship for application (status -> 'open').
    Notifies all active students.
    """
    _inherit = 'education.scholarship'
    def action_open(self):
        """Override action_open to notify all students when scholarship opens."""
        res = super().action_open()
        # Get all active students (res.partner with position_role = 'student')
        students = self.env['res.partner'].sudo().search([
            ('position_role', '=', 'student'),
            ('active', '=', True),
        ])
        if students:
            recipient_ids = [(4, s.id) for s in students]
            notif = self.env['edu.notification'].sudo().create({
                'name': f'New Scholarship: {self.name}',
                'message': (
                    f'A new scholarship "{self.name}" is now open for applications. '
                    f'Please check the Published Scholarships section.'
                ),
                'recipient_ids': recipient_ids,
                'module': 'scholarship',
                'notification_type': 'in_app',
                'status': 'draft',
            })
            notif.action_send()
        return res

class EducationScholarshipApplicationNotification(models.Model):
    """
    Inherits education.scholarship.application to send portal notifications
    when an application is approved or rejected (via action_check).
    Notifies only the specific student.
    """
    _inherit = 'education.scholarship.application'
    def action_check(self):
        """Override action_check to notify student after approve/reject decision."""
        res = super().action_check()
        partner = self.student_id
        if self.state == 'approved':
            notif = self.env['edu.notification'].sudo().create({
                'name': f'Scholarship Approved: {self.scholarship_id.name}',
                'message': (
                    f'Congratulations! Your application for the scholarship '
                    f'"{self.scholarship_id.name}" has been approved. '
                    f'Please check the Scholarships section for details.'
                ),
                'recipient_ids': [(4, partner.id)],
                'module': 'scholarship',
                'notification_type': 'in_app',
                'status': 'draft',
            })
            notif.action_send()
        elif self.state == 'rejected':
            notif = self.env['edu.notification'].sudo().create({
                'name': f'Scholarship Application Update: {self.scholarship_id.name}',
                'message': (
                    f'Your application for the scholarship "{self.scholarship_id.name}" '
                    f'was not approved at this time. '
                ),
                'recipient_ids': [(4, partner.id)],
                'module': 'scholarship',
                'notification_type': 'in_app',
                'status': 'draft',
            })
            notif.action_send()
        return res