from odoo.addons.portal.controllers.portal import CustomerPortal
from odoo.http import request
from .portal_utils import get_student_partner



class CustomPortalDashboard(CustomerPortal):

    def _prepare_home_portal_values(self, counters):
        # Get default values first
        values = super()._prepare_home_portal_values(counters)
        partner = get_student_partner()
        if not partner:
            return values
        values['position_role'] = partner.position_role
        return values