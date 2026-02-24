# education_mobile_and_portal_access/models/inherited_notification.py
from odoo import models, fields

class EduNotificationInherit(models.Model):
    # This refers to the model name inside your Notification module
    _inherit = "edu.notification"

    # We add this field ONLY when the portal module is installed
    read_by_partner_ids = fields.Many2many(
        'res.partner',
        'edu_notif_portal_read_rel',
        string="Read By Portal Users"
    )