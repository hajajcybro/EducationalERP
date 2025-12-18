from odoo import models, fields,_

class EducationDocumentRejectWizard(models.TransientModel):
    _name = 'education.document.reject.wizard'
    _description = 'Reject Education Document'

    rejection_reason = fields.Text(
        string='Rejection Reason',
        required=True
    )
    document_id = fields.Many2one(
        'education.document',
        string='Document',
        required=True,
        readonly=True
    )
    def action_confirm_reject(self):
        """Reject the document and update its state to 'rejected'.
        Notify the student via email with the rejection reason and re-upload request."""
        document = self.document_id
        document.write({'state': 'rejected'})

        student = document.student_id
        subject = _("Document Rejected")

        body_html = """
                    <p>Dear %s,</p>

                    <p>Your document has been <b>rejected</b>.</p>

                    <p><b>Reason:</b><br/>%s</p>

                    <p>Please re-upload the corrected document.</p>

                    <p>Regards,<br/>
                    %s</p>
                """ % (
            student.name or '',
            self.rejection_reason,
            self.env.user.name
        )

        mail = self.env['mail.mail'].create({
            'subject': subject,
            'email_to': student.email,
            'body_html': body_html,
        })
        mail.send()
        return {'type': 'ir.actions.act_window_close'}


