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
        string="Version",
        default=1,
        readonly=True
    )
    # expiry manage
    is_expirable = fields.Boolean(
        string="Is Expirable",
        related='document_type.is_expirable',
        store=True,
        readonly=True
    )
    expiry_date = fields.Date(
        string="Expiry Date"
    )

    @api.onchange('document_type', 'issue_date')
    def _onchange_document_type_expiry(self):
        """ Compute the expiry date automatically based on the document type
        validity period and the selected issue date."""
        for record in self:
            record.expiry_date = False
            if (
                    record.issue_date
                    and record.document_type
                    and record.is_expirable
                    and record.document_type.validity_days
            ):
                record.expiry_date = record.issue_date + timedelta(
                    days=record.document_type.validity_days
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

    @api.model
    def cron_check_document_expiry(self):
        """
        Single scheduled job that:
        - Sends warning email exactly 2 days before expiry
        - Sends expired email after expiry
        """
        today = fields.Date.today()
        warning_date = today + timedelta(days=2)

        documents = self.search([
            ('is_expirable', '=', True),
            ('expiry_date', '!=', False),
            ('state', '=', 'approved'),
        ])

        warning_students = {}
        expired_students = {}

        for doc in documents:
            student = doc.student_id
            if not student or not student.email:
                continue

            if doc.expiry_date == warning_date:
                warning_students.setdefault(student, []).append(doc)

            elif doc.expiry_date <= today:
                expired_students.setdefault(student, []).append(doc)

        # Send warning emails (2 days before expiry)
        for student, docs in warning_students.items():
            self._send_warning_email(student, docs)

        # Send expired emails
        for student, docs in expired_students.items():
            self._send_expired_email(student, docs)

    def _send_warning_email(self, student, documents):
        """
        Send polite warning email for documents
        expiring exactly 2 days from today.
        """
        today = fields.Date.today()
        doc_list = ""
        for doc in documents:
            print(doc)
            days_left = (doc.expiry_date - today).days
            doc_list += (
                f"<li>"
                f"<b>{doc.document_type.name}</b> – "
                f"Expiry Date: {doc.expiry_date} "
                f"({days_left} days remaining)"
                f"</li>"
            )
        body_html = f"""
            <p>Dear {student.name},</p>
            <p>
                This is a friendly reminder that the following document(s)
                are nearing their expiry date.
            </p>
            <ul>{doc_list}</ul>
            <p>
                Kindly ensure that the required documents are renewed
                and uploaded before the expiry date to avoid any inconvenience.
            </p>
            <p>
                Regards,<br/>
                Administration
            </p>
        """
        self.env['mail.mail'].create({
            'subject': _("Document Expiry Alert"),
            'email_to': student.email,
            'body_html': body_html,
        }).send()

    def _send_expired_email(self, student, documents):
        """
        Send urgent email notification for expired documents.
        This is triggered only after the document is expired.
        """
        today = fields.Date.today()
        doc_list = ""
        for doc in documents:
            days_ago = (today - doc.expiry_date).days
            doc_list += (
                f"<li>"
                f"<b>{doc.document_type.name}</b> – "
                f"Expired on {doc.expiry_date} "
                f"({days_ago} day(s) ago)"
                f"</li>"
            )
        body_html = f"""
            <p>Dear {student.name},</p>
            <p style="color:red;">
                <b>URGENT: ACTION REQUIRED</b>
            </p>
            <p>
                The following document(s) have expired and are no longer valid:
            </p>
            <ul>{doc_list}</ul>
            <p>
                Please upload renewed documents immediately to avoid
                any interruption or compliance issues.
            </p>
            <p>
                Regards,<br/>
                Administration
            </p>
        """
        self.env['mail.mail'].create({
            'subject': _("URGENT: Expired Documents"),
            'email_to': student.email,
            'body_html': body_html,
        }).send()

    @api.model_create_multi
    def create(self, vals_list):
        today = fields.Date.today()

        for vals in vals_list:
            student_id = vals.get('student_id')
            document_type = vals.get('document_type')

            if student_id and document_type:
                # Block upload if approved & valid document exists
                approved_doc = self.search([
                    ('student_id', '=', student_id),
                    ('document_type', '=', document_type),
                    ('state', '=', 'approved'),
                    '|',
                    ('expiry_date', '=', False),
                    ('expiry_date', '>=', today),
                ], limit=1)

                if approved_doc:
                    raise ValidationError(
                        _("An approved and valid document already exists. "
                          "You can upload a new version only after rejection or expiry.")
                    )

                # Auto-increment version
                last_doc = self.search([
                    ('student_id', '=', student_id),
                    ('document_type', '=', document_type),
                ], order='version desc', limit=1)

                vals['version'] = last_doc.version + 1 if last_doc else 1

        return super().create(vals_list)

