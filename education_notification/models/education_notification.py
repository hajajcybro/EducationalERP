from odoo import fields, models, api

class EduNotification(models.Model):
    _name = "edu.notification"
    _description = "Education Notification"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "scheduled_date desc"

    name = fields.Char(required=True, tracking=True)
    message = fields.Text(required=True)
    recipient_ids = fields.Many2many("res.partner", string="Recipients")
    notification_type = fields.Selection([
        ("email", "Email"),
        ("sms", "SMS"),
        ("in_app", "In-App"),
        ("multi", "Multi Channel"),
    ], required=True, default="in_app")
    module = fields.Selection([
        ("attendance", "Attendance"),
        ("financial", "financial"),
        ("exam", "Exam"),
        ("hostel", "Hostel"),
        ("transport", "Transport"),
        ("library", "Library"),
        ("scholarship", "Scholarship"),
        ("document", "Document"),
        ("alumni", "Alumni"),
        ("general", "General"),
    ], default="general")
    status = fields.Selection([
        ("draft", "Draft"),
        ("pending", "Pending"),
        ("sent", "Sent"),
        ("failed", "Failed"),
    ], default="draft", tracking=True,copy=False)
    scheduled_date = fields.Datetime(default=fields.Datetime.now)
    sent_date = fields.Datetime()
    retry_count = fields.Integer(default=0)
    max_retry = fields.Integer(default=3)
    created_by = fields.Many2one("res.users",
        default=lambda self: self.env.user)
    marketing_mailing_id = fields.Many2one(
        "mailing.mailing",
        string="Marketing Campaign",
        readonly=True,copy=False
    )
    is_sms = fields.Boolean(
        string="Is SMS Campaign",
        readonly=True,copy=False
    )
    class_id = fields.Many2one('education.class', string="Class", help='Choose a class to send mail/SMS to a particular class.')
    # Tracks which students have viewed this notification in the portal
    read_by_partner_ids = fields.Many2many('res.partner', 'edu_notif_read_rel', string="Read By Portal Users")
    academic_year_id = fields.Many2one(
        'education.academic.year',
        string='Academic Year',
        help="Select the academic year to notify past students/alumni."
    )
    @api.onchange('class_id')
    def _onchange_class_id(self):
        self.recipient_ids  = self.class_id.student_ids

    @api.onchange('academic_year_id', 'module')
    def _onchange_academic_year_id(self):
        if self.academic_year_id:
            domain = [('academic_year_id', '=', self.academic_year_id.id)]
            partners = self.env['res.partner'].search(domain)
            self.recipient_ids = partners

    def action_send(self):
        self.ensure_one()
        try:
            mailing = False
            if self.notification_type == "email":
                mailing = self._send_email()
            elif self.notification_type == "sms":
                mailing = self._send_sms()
            elif self.notification_type == "multi":
                self._send_email()
                self._send_sms()
                self._send_in_app()
            self.status = "pending"
            self.sent_date = fields.Datetime.now()
            if mailing:
                return {
                    "type": "ir.actions.act_window",
                    "res_model": "mailing.mailing",
                    "res_id": mailing.id,
                    "view_mode": "form",
                    "target": "current",
                }
        except Exception as e:
            self.retry_count += 1
            self.status = "failed"
            self.env["edu.notification.log"].create({
                "notification_id": self.id,
                "error_message": str(e),
            })

    def _send_notification(self):
        if self.notification_type in ("email", "multi"):
            self._send_email()
        if self.notification_type in ("sms", "multi"):
            self._send_sms()
        if self.notification_type in ("in_app", "multi"):
            self._send_in_app()

    def _send_email(self):
        self.ensure_one()
        partners = self.recipient_ids.filtered("email")
        if not partners:
            return False
        mailing = self.env["mailing.mailing"].create({
            "name": self.name,
            "subject": self.name,
            "mailing_type": "mail",
            "state": "draft",
            "mailing_model_id": self.env.ref("base.model_res_partner").id,
            "mailing_model_real": "res.partner",
            "body_arch": f"""
                <t t-name="mailing.body">
                    <div style="font-size:14px;">
                        <p>{self.message}</p>
                    </div>
                </t>
            """,
            "mailing_domain": str([("id", "in", partners.ids)]),
            "edu_notification_id": self.id,
            "is_edu_notification": True,
        })
        self.marketing_mailing_id = mailing.id
        self.is_sms = False
        return mailing

    def _send_sms(self):
        self.ensure_one()
        partners = self.recipient_ids.filtered("phone")
        if not partners:
            return False
        mailing = self.env["mailing.mailing"].create({
            "name": self.name,
            "subject": self.name,
            "mailing_type": "sms",
            "state": "draft",
            "mailing_model_id": self.env.ref("base.model_res_partner").id,
            "mailing_model_real": "res.partner",
            "body_plaintext": self.message,
            "mailing_domain": str([("id", "in", partners.ids)]),
            "edu_notification_id": self.id,
            "is_edu_notification": True,
        })
        self.marketing_mailing_id = mailing.id
        self.is_sms = True
        return mailing

    def _send_in_app(self):
        self.ensure_one()

        partners = self.recipient_ids
        if not partners:
            return

        self.message_post(
            body=self.message,
            partner_ids=partners.ids,
            message_type="notification",
            subtype_xmlid="mail.mt_comment",
        )

    def action_open_marketing(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "res_model": "mailing.mailing",
            "res_id": self.marketing_mailing_id.id,
            "view_mode": "form",
        }
