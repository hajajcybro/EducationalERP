from odoo.addons.portal.controllers.portal import CustomerPortal
from odoo.http import request


class CustomPortalDashboard(CustomerPortal):

    def _prepare_home_portal_values(self, counters):
        # Get default values first
        values = super()._prepare_home_portal_values(counters)
        partner = request.env.user.partner_id
        values['position_role'] = partner.position_role
        return values