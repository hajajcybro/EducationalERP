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
            ('guardian', '=', partner.id),
            ('position_role', '=', 'student')
        ], limit=1)
        return student
    # Return empty recordset if nothing found
    return request.env['res.partner']

def get_alumni_partner():
    """
    Returns the correct alumni res.partner for the logged-in user.
      - Alumni → returns own partner
      - Others → returns empty recordset
    """
    partner = request.env.user.partner_id
    if partner.position_role == 'alumni':
        return partner
    return request.env['res.partner']

def get_portal_redirect(partner):
    """
    Given a partner, return the correct portal home URL based on role.
    Use this to guard routes — redirect if wrong role lands on wrong page.

    Usage:
        partner = request.env.user.partner_id
        if partner.position_role != 'alumni':
            return request.redirect(get_portal_redirect(partner))
    """
    role = partner.position_role if partner else None
    if role == 'student':
        return '/my/profile'
    elif role == 'parent':
        return '/my/profile'
    elif role == 'alumni':
        return '/my/alumni'
    return '/my'
