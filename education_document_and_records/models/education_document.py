from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta



class EducationDocument(models.Model):
    _inherit = 'education.document'

    faculty_id = fields.Many2one(
        'hr.employee', domain=[('role', '=', 'teacher')],
        string='Faculty'
    )
    program_id = fields.Many2one(
        'education.program',
        string='Program'
    )
    uploaded_by = fields.Many2one(
        'res.users',
        default=lambda self: self.env.user,
    )
    upload_date = fields.Datetime(
        default=fields.Datetime.now,
        readonly=True
    )
    state = fields.Selection([
        ('draft','draft'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ], default='draft', tracking=True)
    version = fields.Integer(
        default=1,
        tracking=True
    )


    def action_approve_doc(self):
        """Mark the document as approved and finalized """
        for record in self:
            record.state ='approved'

    def write(self, vals):
        """Block updates once the document is approved."""
        if self.state == 'approved':
            allowed = {'state'}
            if not set(vals).issubset(allowed):
                raise ValidationError(
                    "Documents  cannot be modified."
                )
        return super().write(vals)

    def action_reject_doc(self):
        """Open the document rejection wizard."""
        self.ensure_one()
        return {
            'name': 'Reject Document',
            'type': 'ir.actions.act_window',
            'res_model': 'education.document.reject.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_document_id': self.id,
            }
        }


    @api.model
    def cron_check_mandatory_documents(self):
        """ Check missing mandatory documents and notify students """
        documentType = self.env['education.document.type']
        Partner = self.env['res.partner']
        students = Partner.search([
            ('is_student', '=', True),
            ('email', '!=', False),
        ])
        mandatory_types = documentType.search([
            ('is_mandatory', '=', True)
        ])
        today = fields.Date.today()
        if mandatory_types:
            for student in students:
                last_mail_date = student.last_missing_doc_mail_date
                for doc_type in mandatory_types:
                    exists = self.search_count([
                        ('student_id', '=', student.id),
                        ('document_type', '=', doc_type.id),
                    ])
                    if not exists:
                        interval = doc_type.reminder_interval_days
                        if last_mail_date:
                            print('yesaa')
                            next_allowed_date = last_mail_date + timedelta(days=interval)
                            if today >= next_allowed_date:
                                print('before')
                                self._notify_missing_document(
                                    student, doc_type, gentle=True
                                )
                                student.sudo().write({
                                    'last_missing_doc_mail_date': today + timedelta(days=9999)
                                })
                        self._notify_missing_document(student, doc_type)
                        student.write({'last_missing_doc_mail_date': today})

    def _notify_missing_document(self, student, doc_type, gentle=False):
        """ Send missing mandatory document reminder to student"""
        print('send')

        if gentle:
            subject = _("Gentle Reminder: Pending Document – %s") % doc_type.name
            intro = _("This is a gentle reminder that the following document is still pending.")
        else:
            subject = _("Mandatory Document Required: %s") % doc_type.name
            intro = _("Please upload the following mandatory document.")

        body_html = """
            <p>Dear %s,</p>

            <p>%s</p>
    
            <p><b>Document:</b> %s</p>
    
            <p>Please upload it at your convenience.</p>
    
            <p>Regards,<br/>Administration</p>
        """ % (
            student.name or '',
            intro,
            doc_type.name or ''
        )

        self.env['mail.mail'].create({
            'subject': subject,
            'email_to': student.email,
            'body_html': body_html,
        }).send()
