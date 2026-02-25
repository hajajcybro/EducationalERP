from odoo import models, fields, api
class EducationDocumentNotification(models.Model):
    """
    Inherits education.document to send portal in-app notifications:
    1. action_approve_doc  → Document approved by admin
    2. action_reject_doc      → Document reject by admin
    4. _send_warning_email  → Document expiring in 2 days
    """
    _inherit = 'education.document'


    # 1. Admin approves a document uploaded from portal
    def action_approve_doc(self):
        res = super().action_approve_doc()
        partner = self.student_id  # res.partner directly
        if partner:
            notif = self.env['edu.notification'].sudo().create({
                'name': f'Document Approved: {self.document_type.name}',
                'message': (
                    f'Your document "{self.document_type.name}" has been approved.'),
                'recipient_ids': [(4, partner.id)],
                'module': 'document',
                'notification_type': 'in_app',
                'status': 'draft',
            })
            notif.action_send()
        return res

    # 2. Admin rejects a document (via reject wizard state change)
    def action_reject_doc(self):
        res = super().action_reject_doc()
        return res

    def write(self, vals):
        # Catch state → 'rejected' to send portal notification
        if vals.get('state') == 'rejected':
            for rec in self:
                partner = rec.student_id
                if partner:
                    notif = self.env['edu.notification'].sudo().create({
                        'name': f'Document Rejected: {rec.document_type.name}',
                        'message': (
                            f'Your document "{rec.document_type.name}" was not approved. '
                            f'Please upload a new version.'
                        ),
                        'recipient_ids': [(4, partner.id)],
                        'module': 'document',
                        'notification_type': 'in_app',
                        'status': 'draft',
                    })
                    notif.action_send()
        return super().write(vals)

    # 5. Document expiring in 2 days
    def _send_warning_email(self, student, documents):
        # Call original email method
        super()._send_warning_email(student, documents)

        today = fields.Date.today()
        for doc in documents:
            days_left = (doc.expiry_date - today).days
            notif = self.env['edu.notification'].sudo().create({
                'name': f'Document Expiring Soon: {doc.document_type.name}',
                'message': (
                    f'Your document "{doc.document_type.name}" will expire in '
                    f'{days_left} day(s) on {doc.expiry_date}. '
                    f'Please upload a renewed version from your Profile section.'
                ),
                'recipient_ids': [(4, student.id)],
                'module': 'document',
                'notification_type': 'in_app',
                'status': 'draft',
            })
            notif.action_send()

