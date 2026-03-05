# controllers/portal_utils.py
from odoo.http import request


def get_student_partner():
    """
    Shared helper to find the correct student record.
    1. If logged in user is Student -> Return user.
    2. If logged in user is Parent -> Return their Child.
    3. If neither -> Return empty recordset.
    """
    partner = request.env.user.partner_id
    if partner.position_role == 'student':
        return partner
    elif partner.position_role == 'parent':
        # Find the student who has this user as their guardian
        student = request.env['res.partner'].sudo().search([
            ('guardian_id', '=', partner.id),
            ('position_role', '=', 'student')
        ], limit=1)
        return student
    # Return empty recordset if nothing found
    return request.env['res.partner']