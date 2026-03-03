from odoo import models, fields, api
from odoo.http import request
from odoo.exceptions import AccessDenied
import logging

_logger = logging.getLogger(__name__)

class ResUsers(models.Model):
    _inherit = 'res.users'

    def action_reset_password(self):
        # Step 1: Odoo default — sends the reset email
        result = super().action_reset_password()
        ip_address = request.httprequest.environ.get('HTTP_X_FORWARDED_FOR')
        if not ip_address:
            ip_address = request.httprequest.remote_addr
        for user in self:
            self.env['education.audit.log'].sudo().create({
                'user_id':     user.id,
                'action_type': 'password_reset',
                'model_name':  'res.users',
                'record_id':   user.id,
                'ip_address': ip_address,
                'description': (
                    f'Password reset email sent to: {user.login}'
                ),
                'source':      'portal',
                'severity':    'info',
            })
        return result

    def _login(self, credential, user_agent_env):
        """
        Odoo 19: _login is a regular instance method.
        credential = {'login': '...', 'password': '...', 'type': 'password'}
        """
        try:
            # SUCCESS — do NOT log, return normally
            return super()._login(credential, user_agent_env)

        except AccessDenied:
            try:
                login = credential.get('login', '')

                ip_address = None
                try:
                    ip_address = request.httprequest.environ.get('HTTP_X_FORWARDED_FOR')
                    if not ip_address:
                        ip_address = request.httprequest.remote_addr
                except Exception:
                    pass

                # Check if login exists in system
                user = self.sudo().search([('login', '=', login)], limit=1)

                if user:
                    description = f'Failed login attempt for user: {login}'
                else:
                    description = f'Failed login attempt with unrecognized login: {login}'

                self.env['education.audit.log'].sudo().create({
                    'user_id': user.id if user else self.env.ref('base.public_user').id,
                    'action_type': 'failed_login',
                    'model_name': 'res.users',
                    'record_id': user.id if user else 0,
                    'description': description,
                    'ip_address': ip_address,
                    'source': 'portal',
                    'severity': 'warning',
                })
            except Exception as e:
                _logger.error("Audit log error on failed login: %s", str(e))
            raise

    def action_force_logout(self, reason=None):
        self.ensure_one()

        ip_address = None
        try:
            ip_address = request.httprequest.remote_addr
        except Exception:
            pass
        self.env['education.audit.log'].sudo().create({
            'user_id': self.id,
            'action_type': 'force_logout',
            'model_name': 'res.users',
            'record_id': self.id,
            'description': (
                f'User "{self.name}" ({self.login}) forcefully logged out '
                f'by Admin: {self.env.user.name}. '
                f'Reason: {reason or "No reason provided"}'
            ),
            'ip_address': ip_address,
            'source': 'internal',
            'severity': 'warning',
        })
        self.sudo()._invalidate_session()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Force Logout',
                'message': f'"{self.name}" has been logged out successfully.',
                'type': 'success',
                'sticky': False,
            }
        }