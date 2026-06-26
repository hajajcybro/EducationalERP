# -*- coding: utf-8 -*-
"""
education.portal.password.wizard
=================================
Lets an education administrator set / reset the portal login password for a
student's portal user.

NOTE: Odoo stores passwords hashed, so an existing password can never be
displayed. This wizard therefore sets a *new* password and shows it to the
admin at the moment of creation, so it can be shared with the student. A
strong password is pre-filled by default; the admin may overwrite it.
"""
import secrets
import string

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class PortalPasswordWizard(models.TransientModel):
    _name = "education.portal.password.wizard"
    _description = "Set Portal Password Wizard"

    enrollment_id = fields.Many2one(
        "education.enrollment",
        string="Enrollment",
        required=True,
        readonly=True,
    )
    user_id = fields.Many2one(
        "res.users",
        string="Portal User",
        required=True,
        readonly=True,
    )
    login = fields.Char(
        string="Login",
        related="user_id.login",
        readonly=True,
    )
    new_password = fields.Char(
        string="New Password",
        required=True,
        default=lambda self: self._generate_password(),
        help="The student uses this to log in to the portal. Copy it now and "
             "share it securely — it cannot be viewed again once saved.",
    )

    @api.model
    def _generate_password(self):
        """Return a readable, reasonably strong random password."""
        alphabet = string.ascii_letters + string.digits
        return "".join(secrets.choice(alphabet) for _ in range(10))

    def action_set_password(self):
        self.ensure_one()
        if not self.new_password or len(self.new_password) < 8:
            raise UserError(_("Password must be at least 8 characters long."))
        # Education admins are not necessarily Odoo system administrators, so
        # write the password with elevated rights. The button that opens this
        # wizard is already restricted to the education admin group.
        self.user_id.sudo().write({"password": self.new_password})
        self.enrollment_id.message_post(
            body=_("Portal password was reset by %s.") % self.env.user.name
        )
        return {"type": "ir.actions.act_window_close"}
