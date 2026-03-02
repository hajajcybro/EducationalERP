# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from datetime import timedelta


class EducationLibraryTransaction(models.Model):
    _name = 'education.library.transaction'
    _description = 'Library Transaction'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'issue_date desc'

    name = fields.Char(string='Transaction#', required=True, copy=False, readonly=True, default='New')
    book_id = fields.Many2one(comodel_name='education.library.book', string='Book', required=True, tracking=True)
    member_id = fields.Many2one(comodel_name='education.library.member', string='Member', required=True, tracking=True)
    issue_date = fields.Date(string='Issue Date', tracking=True)
    due_date = fields.Date(string='Due Date', tracking=True)
    return_date = fields.Date(string='Return Date', tracking=True)
    days_overdue = fields.Integer(string='Days Overdue', compute='_compute_days_overdue', store=True)
    fine_amount = fields.Float(string='Fine', compute='_compute_fine_amount', store=True)
    fine_per_day = fields.Float(string='Fine/Day')
    status = fields.Selection([
        ('draft', 'Draft'),
        ('issued', 'Issued'),
        ('returned', 'Returned'),
        ('overdue', 'Overdue'),
        ('lost', 'Lost')
    ], string='Status', compute='_compute_status', store=True, default='draft', tracking=True)
    notes = fields.Text(string='Notes')
    book_title = fields.Char(related='book_id.title', string='Book Title', readonly=True)
    member_name = fields.Char(related='member_id.name', string='Member Name', readonly=True)
    isbn = fields.Char(related='book_id.isbn', string='ISBN', readonly=True)
    renewal_count = fields.Integer(string='Renewals', default=0, tracking=True)
    max_renewals = fields.Integer(string='Max Renewals')
    reservation_id = fields.Many2one(comodel_name='education.library.reservation', string='From Reservation', readonly=True)
    is_from_reservation = fields.Boolean(string='From Reservation', compute='_compute_is_from_reservation', store=True)
    due_reminder_sent = fields.Boolean(string='Due Reminder Sent', default=False, copy=False)
    overdue_notification_sent = fields.Boolean(string='Overdue Notification Sent', default=False, copy=False)

    @api.depends('reservation_id')
    def _compute_is_from_reservation(self):
        for transaction in self:
            transaction.is_from_reservation = bool(transaction.reservation_id)

    @api.depends('due_date', 'return_date', 'issue_date')
    def _compute_status(self):
        today = fields.Date.today()
        for transaction in self:
            if not transaction.issue_date:
                transaction.status = 'draft'
                continue

            if transaction.return_date:
                if transaction.id:
                    old_status = self.env['education.library.transaction'].browse(transaction.id).status
                    if old_status == 'lost':
                        transaction.status = 'lost'
                        continue
                transaction.status = 'returned'
            elif transaction.due_date and today > transaction.due_date:
                transaction.status = 'overdue'
            else:
                transaction.status = 'issued'

    @api.model_create_multi
    def create(self, vals_list):
        ICP = self.env['ir.config_parameter'].sudo()

        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('education.library.transaction') or 'New'

            # Set fine_per_day from settings if not provided
            if 'fine_per_day' not in vals or not vals.get('fine_per_day'):
                vals['fine_per_day'] = float(ICP.get_param('education_library.fine_per_day', 5.0))

            # Set max_renewals from settings if not provided
            if 'max_renewals' not in vals or not vals.get('max_renewals'):
                vals['max_renewals'] = int(ICP.get_param('education_library.max_renewals', 2))

        transactions = super().create(vals_list)
        return transactions

    @api.depends('due_date', 'return_date', 'status')
    def _compute_days_overdue(self):
        today = fields.Date.today()
        for transaction in self:
            if not transaction.due_date:
                transaction.days_overdue = 0
                continue

            if transaction.status == 'returned' and transaction.return_date:
                if transaction.return_date > transaction.due_date:
                    transaction.days_overdue = (transaction.return_date - transaction.due_date).days
                else:
                    transaction.days_overdue = 0
            elif transaction.status in ['issued', 'overdue']:
                if today > transaction.due_date:
                    transaction.days_overdue = (today - transaction.due_date).days
                else:
                    transaction.days_overdue = 0
            else:
                transaction.days_overdue = 0

    @api.depends('days_overdue', 'fine_per_day')
    def _compute_fine_amount(self):
        for transaction in self:
            transaction.fine_amount = transaction.days_overdue * transaction.fine_per_day

    @api.onchange('issue_date', 'member_id')
    def _onchange_issue_date(self):
        if self.status != 'draft' and self.issue_date and self.member_id:
            ICP = self.env['ir.config_parameter'].sudo()

            if self.member_id.member_type in ['faculty', 'staff']:
                days = int(ICP.get_param('education_library.faculty_borrow_days', 30))
            else:
                days = int(ICP.get_param('education_library.student_borrow_days', 14))

            self.due_date = self.issue_date + timedelta(days=days)

    @api.onchange('book_id')
    def _onchange_book_id(self):
        if self.book_id:
            if self.book_id.copies_available <= 0:
                available_reservation = self.env['education.library.reservation'].search([
                    ('book_id', '=', self.book_id.id),
                    ('member_id', '=', self.member_id.id),
                    ('status', '=', 'available')
                ], limit=1)

                if not available_reservation:
                    return {
                        'warning': {
                            'title': _('No Copies Available'),
                            'message': _('This book has no available copies. You can reserve it instead.')
                        }
                    }

    @api.onchange('member_id')
    def _onchange_member_id(self):
        if self.member_id and self.member_id.is_expired:
            return {
                'warning': {
                    'title': _('Member Expired'),
                    'message': _('This member\'s membership has expired on %s') % self.member_id.expiry_date
                }
            }

    @api.constrains('issue_date', 'due_date', 'return_date')
    def _check_dates(self):
        for transaction in self:
            if transaction.due_date and transaction.issue_date and transaction.due_date < transaction.issue_date:
                raise ValidationError(_('Due date cannot be before issue date!'))
            if transaction.return_date and transaction.issue_date and transaction.return_date < transaction.issue_date:
                raise ValidationError(_('Return date cannot be before issue date!'))

    def action_issue_book(self):
        """Issue the book - change from draft to issued"""
        ICP = self.env['ir.config_parameter'].sudo()

        for transaction in self:
            if transaction.status != 'draft':
                raise UserError(_('Only draft transactions can be issued!'))

            available_reservation = self.env['education.library.reservation'].search([
                ('book_id', '=', transaction.book_id.id),
                ('member_id', '=', transaction.member_id.id),
                ('status', '=', 'available')
            ], limit=1)

            if not available_reservation and transaction.book_id.copies_available <= 0:
                raise UserError(_('No copies available for "%s"! Please reserve the book.') % transaction.book_id.title)
            if transaction.member_id.is_expired:
                raise UserError(_('Member "%s" membership has expired!') % transaction.member_id.name)

            issue_date = fields.Date.today()

            # Get borrow days from settings
            if transaction.member_id.member_type in ['faculty', 'staff']:
                days = int(ICP.get_param('education_library.faculty_borrow_days', 30))
            else:
                days = int(ICP.get_param('education_library.student_borrow_days', 14))

            due_date = issue_date + timedelta(days=days)

            transaction.write({
                'issue_date': issue_date,
                'due_date': due_date,
                'reservation_id': available_reservation.id if available_reservation else False
            })

            if available_reservation:
                available_reservation.action_mark_fulfilled(transaction.id)

            transaction.book_id._compute_copies()
            if transaction.book_id.copies_available == 0:
                transaction.book_id.state = 'issued'
            transaction.message_post(
                body=_('Book issued to %s on %s. Due date: %s%s') % (
                    transaction.member_id.name,
                    issue_date,
                    due_date,
                    ' (From Reservation)' if available_reservation else ''
                )
            )

    def action_return_book(self):
        """Return the book and check for pending reservations"""
        self.ensure_one()
        if self.status not in ['issued', 'overdue']:
            raise UserError(_('Only issued or overdue books can be returned!'))

        self.write({'return_date': fields.Date.today()})
        self.book_id._compute_copies()

        if self.book_id.has_reservations:
            next_reservation = self.book_id._allocate_to_next_reservation()
            if next_reservation:
                self.message_post(
                    body=_('Book returned. Fine: %s. Allocated to next reservation: %s (Queue Position: %s)') %
                         (self.fine_amount, next_reservation.member_id.name, next_reservation.priority)
                )
            else:
                self.message_post(body=_('Book returned. Fine: %s') % self.fine_amount)
        else:
            if self.book_id.copies_available > 0:
                self.book_id.state = 'available'
            self.message_post(body=_('Book returned. Fine: %s') % self.fine_amount)
        # Send in-app notification only if a fine was generated
        if self.fine_amount > 0:
            partner = self.member_id.partner_id
            if partner:
                notif = self.env['edu.notification'].sudo().create({
                    'name': f'Library Fine: {self.book_id.title}',
                    'message': (
                        f'You have a fine of ₹{self.fine_amount} for the late return of '
                        f'"{self.book_id.title}" ({self.days_overdue} day(s) overdue). '
                        f'Please check the ActivityF section for details.'
                    ),
                    'recipient_ids': [(4, partner.id)],
                    'module': 'library',
                    'notification_type': 'in_app',
                    'status': 'draft',
                })
                notif.action_send()

    def action_renew(self):
        """Renew the book - extend due date"""
        self.ensure_one()
        ICP = self.env['ir.config_parameter'].sudo()

        if self.status not in ['issued', 'overdue']:
            raise UserError(_('Only issued or overdue books can be renewed!'))
        if self.renewal_count >= self.max_renewals:
            raise UserError(_('Maximum renewals (%s) reached! Cannot renew further.') % self.max_renewals)
        if self.book_id.has_reservations:
            raise UserError(
                _('Cannot renew. There are %s pending reservations for this book.') %
                self.book_id.pending_reservations
            )

        # Get borrow days from settings
        if self.member_id.member_type in ['faculty', 'staff']:
            days = int(ICP.get_param('education_library.faculty_borrow_days', 30))
        else:
            days = int(ICP.get_param('education_library.student_borrow_days', 14))

        new_due_date = self.due_date + timedelta(days=days)

        self.write({
            'due_date': new_due_date,
            'renewal_count': self.renewal_count + 1,
            'due_reminder_sent': False
        })
        self.message_post(
            body=_('Book renewed. New due date: %s (Renewal #%s of %s)') % (new_due_date, self.renewal_count,
                                                                            self.max_renewals))

    def action_mark_lost(self):
        """Mark book as lost"""
        self.ensure_one()
        if self.status not in ['issued', 'overdue']:
            raise UserError(_('Only issued or overdue books can be marked as lost!'))

        self.write({'return_date': fields.Date.today()})
        self.sudo().write({'status': 'lost'})
        self.book_id.copies_total -= 1
        self.book_id._compute_copies()

        if self.book_id.copies_available > 0:
            self.book_id.state = 'available'
        elif self.book_id.copies_total == 0:
            self.book_id.state = 'lost'
        self.message_post(body=_('Book marked as lost.'))

    # Email notification methods remain the same...
    def _send_due_date_reminder(self):
        """Send reminder that book is due tomorrow"""
        self.ensure_one()

        # Check settings if reminders are enabled
        ICP = self.env['ir.config_parameter'].sudo()
        if not ICP.get_param('education_library.send_due_reminders', True):
            return

        if not self.member_id.email:
            self.message_post(body=_('Cannot send reminder - member has no email address.'))
            return

        try:
            template = self.env.ref('education_library.email_template_transaction_due_reminder')
            template.send_mail(
                self.id,
                force_send=True,
                email_values={
                    'email_to': self.member_id.email,
                    'email_from': self.env.user.email_formatted or self.env.company.email
                }
            )
            self.write({'due_reminder_sent': True})
            self.message_post(body=_('Due date reminder email sent to %s') % self.member_id.email)
        except Exception as e:
            self.message_post(body=_('Failed to send due date reminder: %s') % str(e))

    def _send_overdue_notification(self):
        """Send notification that book is now overdue"""
        self.ensure_one()

        # Check settings if overdue notifications are enabled
        ICP = self.env['ir.config_parameter'].sudo()
        if not ICP.get_param('education_library.send_overdue_notifications', True):
            return

        if not self.member_id.email:
            self.message_post(body=_('Cannot send notification - member has no email address.'))
            return


        try:
            template = self.env.ref('education_library.email_template_transaction_overdue')
            template.send_mail(
                self.id,
                force_send=True,
                email_values={
                    'email_to': self.member_id.email,
                    'email_from': self.env.user.email_formatted or self.env.company.email
                }
            )
            self.write({'overdue_notification_sent': True})
            self.message_post(body=_('Overdue notification email sent to %s') % self.member_id.email)
            partner = self.member_id.partner_id
            if partner:
                notif = self.env['edu.notification'].sudo().create({
                    'name': f'Book Overdue: {self.book_id.title}',
                    'message': (
                        f'Please return the book "{self.book_id.title}" as it is overdue. '
                        f'For further details, please check your Library Activity.'
                    ),
                    'recipient_ids': [(4, partner.id)],
                    'module': 'library',
                    'notification_type': 'in_app',
                    'status': 'draft',
                })
                notif.action_send()
        except Exception as e:
            self.message_post(body=_('Failed to send overdue notification: %s') % str(e))

    @api.model
    def _cron_send_due_date_reminders(self):
        """Cron job to send reminders for books due tomorrow"""
        today = fields.Date.today()
        tomorrow = today + timedelta(days=1)

        due_tomorrow = self.search([
            ('status', '=', 'issued'),
            ('due_date', '=', tomorrow),
            ('due_reminder_sent', '=', False)
        ])

        for transaction in due_tomorrow:
            try:
                transaction._send_due_date_reminder()
            except Exception as e:
                transaction.message_post(body=_('Failed to send due date reminder: %s') % str(e))

    @api.model
    def _cron_send_overdue_notifications(self):
        """Cron job to send notifications for newly overdue books"""
        today = fields.Date.today()

        newly_overdue = self.search([
            ('status', '=', 'overdue'),
            ('due_date', '=', today - timedelta(days=1)),
            ('overdue_notification_sent', '=', False)
        ])

        for transaction in newly_overdue:
            try:
                transaction._send_overdue_notification()
            except Exception as e:
                transaction.message_post(body=_('Failed to send overdue notification: %s') % str(e))