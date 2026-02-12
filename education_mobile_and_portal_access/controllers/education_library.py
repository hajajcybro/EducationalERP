from odoo import http
from odoo.http import request

class LibraryPortal(http.Controller):

    @http.route(['/my/library'], type='http', auth='user', website=True)
    def portal_library_home(self, **kwargs):
        partner = request.env.user.partner_id
        # is_member = partner.is_student
        member = request.env['education.library.member'].sudo().search([
            ('partner_id', '=', partner.id),
            ('state', '=', 'active')
        ], limit=1)
        is_member = bool(member)
        return request.render(
            'education_mobile_and_portal_access.portal_library_home', {
                'is_member': is_member
            }
        )

    @http.route(['/my/library/books'], type='http', auth='user', website=True)
    def portal_library_books(self, **kwargs):
        """Fetches all library books and renders them in the user portal page.
        Accessible only to logged-in users."""
        books = request.env['education.library.book'].sudo().search([])
        return request.render(
            'education_mobile_and_portal_access.portal_library_books', {
                'books': books
            }
        )

    @http.route(['/my/library/history'], type='http', auth='user', website=True)
    def portal_library_history(self, **kwargs):
        partner = request.env.user.partner_id
        member = request.env['education.library.member'].sudo().search([
            ('partner_id', '=', partner.id),
            ('state', '=', 'active')
        ], limit=1)
        print(member)
        transactions = request.env['education.library.transaction'].sudo().search([
            ('member_id', '=', member.id)
        ])
        reservations = request.env['education.library.reservation'].sudo().search([
            ('member_id', '=', member.id)
        ])

        invoices = request.env['account.move'].sudo().search([
            ('library_member_id', '=', member.id),
            ('move_type', '=', 'out_invoice')
        ])

        return request.render(
            'education_mobile_and_portal_access.portal_library_history', {
                'member': member,
                'transactions': transactions,
                'reservations': reservations,
                'invoices': invoices,
            }
        )
