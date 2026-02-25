from odoo import http
from odoo.http import request
from .portal_utils import get_student_partner

class LibraryPortal(http.Controller):

    @http.route(['/my/library'], type='http', auth='user', website=True)
    def portal_library_home(self, **kwargs):
        """
            Render the Library Home page in the portal.
            - Retrieves the logged-in user's partner record.
            - Checks whether the user has an active education.library.member record.
            - Determines membership status based on state = 'active'.
            - Passes the membership flag (is_member) to the template
              to control portal visibility and access options.
            """
        partner = request.env.user.partner_id
        member = request.env['education.library.member'].sudo().search([
            ('partner_id', '=', partner.id),
            ('state', '=', 'active')
        ], limit=1)
        unread_notifications = request.env['edu.notification'].sudo().search([
            ('module', '=', 'library'),
            ('status', 'in', ['pending', 'sent']),
            ('recipient_ids', 'in', partner.id),
            ('read_by_partner_ids', 'not in', partner.id)
        ])
        alert_messages = [n.message for n in unread_notifications if n.message]
        for notif in unread_notifications:
            notif.sudo().write({'read_by_partner_ids': [(4, partner.id)]})
        is_member = bool(member)
        return request.render(
            'education_mobile_and_portal_access.portal_library_home', {
                'is_member': is_member,
                'alert_messages': alert_messages,
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
        """
          Display the Library History page in the portal.
          - Retrieves the logged-in user's partner record.
          - Checks for an active education.library.member record.
          - Fetches all related library transactions (issue/return records).
          - Retrieves book reservations linked to the member.
          - Fetches related customer invoices (account.move with move_type = 'out_invoice')
            generated for library services.
          - Renders the library history template with all related records.
          """
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
