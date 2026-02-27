from odoo import models, fields


class MailingMailing(models.Model):
    _inherit = "mailing.mailing"

    edu_notification_id = fields.Many2one(
        "edu.notification",
        string="Education Notification",
        ondelete="set null",
    )
    is_edu_notification = fields.Boolean(
        string="From Education Notification",
        default=False,
    )

    def action_open_edu_notification(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "res_model": "edu.notification",
            "res_id": self.edu_notification_id.id,
            "view_mode": "form",
        }


