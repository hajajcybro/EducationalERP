# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from datetime import timedelta


class EducationLibraryReservation(models.Model):
    _name = 'education.library.reservation'
    _description = 'Library Book Reservation'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'priority, reservation_date'

    name = fields.Char(string='Reservation#', required=True, copy=False, readonly=True, default='New')
    book_id = fields.Many2one('education.library.book', string='Book', required=True, tracking=True)
    member_id = fields.Many2one('education.library.member', string='Member', required=True, tracking=True)
    reservation_date = fields.Date(string='Reservation Date', default=fields.Date.today, required=True, tracking=True)
    available_date = fields.Date(string='Available Date', tracking=True, readonly=True)
    expiry_date = fields.Date(string='Expiry Date', tracking=True, readonly=True)
    collection_date = fields.Date(string='Collection Date', tracking=True, readonly=True)
    status = fields.Selection([
        ('pending', 'Pending'),
        ('available', 'Available'),
        ('fulfilled', 'Fulfilled'),
        ('expired', 'Expired'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='pending', required=True, tracking=True)
    priority = fields.Integer(string='Queue Position', compute='_compute_priority', store=True)
    transaction_id = fields.Many2one('education.library.transaction', string='Transaction', readonly=True)
    notes = fields.Text(string='Notes')
    book_title = fields.Char(related='book_id.title', string='Book Title', readonly=True)
    member_name = fields.Char(related='member_id.name', string='Member Name', readonly=True)
    isbn = fields.Char(related='book_id.isbn', string='ISBN', readonly=True)
    days_waiting = fields.Integer(string='Days Waiting', compute='_compute_days_waiting')
    is_expiring_soon = fields.Boolean(string='Expiring Soon', compute='_compute_is_expiring_soon')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('education.library.reservation') or 'New'

        reservations = super().create(vals_list)
        for reservation in reservations:
            reservation.message_post(
                body=_('Reservation created. Queue position: %s') % reservation.priority
            )
            reservation._send_created_notification()

        return reservations

    @api.depends('book_id', 'reservation_date', 'status')
    def _compute_priority(self):
        """Calculate queue position for pending reservations"""
        for reservation in self:
            if reservation.status == 'pending':
                earlier_reservations = self.search_count([
                    ('book_id', '=', reservation.book_id.id),
                    ('status', '=', 'pending'),
                    ('reservation_date', '<', reservation.reservation_date),
                    ('id', '!=', reservation.id)
                ])
                reservation.priority = earlier_reservations + 1
            else:
                reservation.priority = 0

    @api.depends('reservation_date', 'status')
    def _compute_days_waiting(self):
        """Calculate how many days member has been waiting"""
        today = fields.Date.today()
        for reservation in self:
            if reservation.status == 'pending' and reservation.reservation_date:
                reservation.days_waiting = (today - reservation.reservation_date).days
            else:
                reservation.days_waiting = 0

    @api.depends('expiry_date', 'status')
    def _compute_is_expiring_soon(self):
        """Check if reservation is expiring within 24 hours"""
        today = fields.Date.today()
        tomorrow = today + timedelta(days=1)
        for reservation in self:
            if reservation.status == 'available' and reservation.expiry_date:
                reservation.is_expiring_soon = reservation.expiry_date <= tomorrow
            else:
                reservation.is_expiring_soon = False

    @api.constrains('book_id', 'member_id', 'status')
    def _check_duplicate_reservation(self):
        """Prevent duplicate active reservations for same book by same member"""
        for reservation in self:
            if reservation.status in ['pending', 'available']:
                duplicate = self.search([
                    ('book_id', '=', reservation.book_id.id),
                    ('member_id', '=', reservation.member_id.id),
                    ('status', 'in', ['pending', 'available']),
                    ('id', '!=', reservation.id)
                ], limit=1)
                if duplicate:
                    raise ValidationError(
                        _('You already have an active reservation for "%s"!') % reservation.book_id.title
                    )

    @api.constrains('member_id')
    def _check_max_reservations(self):
        """Limit maximum active reservations per member"""
        ICP = self.env['ir.config_parameter'].sudo()
        max_reservations = int(ICP.get_param('education_library.max_reservations_per_member', 3))

        for reservation in self:
            if reservation.status in ['pending', 'available']:
                active_count = self.search_count([
                    ('member_id', '=', reservation.member_id.id),
                    ('status', 'in', ['pending', 'available']),
                    ('id', '!=', reservation.id)
                ])
                if active_count >= max_reservations:
                    raise ValidationError(
                        _('Maximum %s active reservations allowed. You currently have %s.') %
                        (max_reservations, active_count)
                    )

    @api.constrains('member_id')
    def _check_member_status(self):
        """Prevent reservations for expired members"""
        for reservation in self:
            if reservation.member_id.is_expired:
                raise ValidationError(
                    _('Cannot create reservation. Member "%s" membership has expired on %s!') %
                    (reservation.member_id.name, reservation.member_id.expiry_date)
                )

    def action_cancel_reservation(self):
        """Cancel a pending reservation"""
        self.ensure_one()
        if self.status not in ['pending', 'available']:
            raise UserError(_('Only pending or available reservations can be cancelled!'))

        old_status = self.status
        self.write({
            'status': 'cancelled'
        })

        self.message_post(body=_('Reservation cancelled by user.'))

        # Send cancellation email
        self._send_cancelled_notification()

        # If this was 'available', make book available for next in queue
        if old_status == 'available':
            self.book_id._allocate_to_next_reservation()

    def action_mark_available(self, expiry_hours=None):
        """Mark reservation as available when book is returned"""
        self.ensure_one()
        ICP = self.env['ir.config_parameter'].sudo()
        if self.status != 'pending':
            raise UserError(_('Only pending reservations can be marked as available!'))

        available_date = fields.Date.today()
        if expiry_hours is None:
            expiry_hours = int(ICP.get_param('education_library.reservation_expiry_hours', 48))

        expiry_date = available_date + timedelta(hours=expiry_hours)
        self.write({
            'status': 'available',
            'available_date': available_date,
            'expiry_date': expiry_date
        })

        self._send_availability_notification()
        self.message_post(
            body=_('Book is now available for collection. Please collect by %s.') % expiry_date
        )

    def action_mark_fulfilled(self, transaction_id):
        """Mark reservation as fulfilled when book is issued"""
        self.ensure_one()
        if self.status != 'available':
            raise UserError(_('Only available reservations can be fulfilled!'))

        self.write({
            'status': 'fulfilled',
            'collection_date': fields.Date.today(),
            'transaction_id': transaction_id
        })

        self.message_post(body=_('Reservation fulfilled. Book issued successfully.'))
        self._send_fulfilled_notification()

    def action_mark_expired(self):
        """Mark reservation as expired and allocate to next in queue"""
        self.ensure_one()
        if self.status != 'available':
            raise UserError(_('Only available reservations can be expired!'))

        self.write({
            'status': 'expired'
        })

        self.message_post(body=_('Reservation expired. Member did not collect the book on time.'))
        self._send_expired_notification()
        self.book_id._allocate_to_next_reservation()

    def _send_created_notification(self):
        """Send notification that reservation was created"""
        self.ensure_one()
        ICP = self.env['ir.config_parameter'].sudo()
        if not ICP.get_param('education_library.send_reservation_notifications', True):
            return

        if not self.member_id.email:
            self.message_post(body=_('Cannot send email - member has no email address.'))
            return

        try:
            template = self.env.ref('education_library.email_template_reservation_created')
            template.send_mail(
                self.id,
                force_send=False,
                email_values={
                    'email_to': self.member_id.email,
                    'email_from': self.env.user.email_formatted or self.env.company.email
                }
            )
            self.message_post(body=_('Reservation confirmation email queued for %s') % self.member_id.email)
        except Exception as e:
            self.message_post(body=_('Failed to send creation email: %s') % str(e))

    def _send_availability_notification(self):
        """Send notification to member that book is available"""
        self.ensure_one()
        ICP = self.env['ir.config_parameter'].sudo()
        if not ICP.get_param('education_library.send_reservation_notifications', True):
            return

        if not self.member_id.email:
            self.message_post(body=_('Cannot send email - member has no email address.'))
            return

        try:
            template = self.env.ref('education_library.email_template_reservation_available')
            template.send_mail(
                self.id,
                force_send=True,
                email_values={
                    'email_to': self.member_id.email,
                    'email_from': self.env.user.email_formatted or self.env.company.email
                }
            )
            self.message_post(body=_('Availability notification email sent to %s') % self.member_id.email)
        except Exception as e:
            self.message_post(body=_('Failed to send availability email: %s') % str(e))

    def _send_expiry_reminder(self):
        """Send reminder that reservation is expiring soon"""
        self.ensure_one()
        ICP = self.env['ir.config_parameter'].sudo()
        if not ICP.get_param('education_library.send_reservation_notifications', True):
            return

        if not self.member_id.email:
            self.message_post(body=_('Cannot send reminder - member has no email address.'))
            return

        try:
            template = self.env.ref('education_library.email_template_reservation_expiry_reminder')
            template.send_mail(
                self.id,
                force_send=True,
                email_values={
                    'email_to': self.member_id.email,
                    'email_from': self.env.user.email_formatted or self.env.company.email
                }
            )
            self.message_post(body=_('Expiry reminder email sent to %s') % self.member_id.email)
        except Exception as e:
            self.message_post(body=_('Failed to send reminder: %s') % str(e))

    def _send_expired_notification(self):
        """Send notification that reservation expired"""
        self.ensure_one()
        ICP = self.env['ir.config_parameter'].sudo()
        if not ICP.get_param('education_library.send_reservation_notifications', True):
            return

        if not self.member_id.email:
            self.message_post(body=_('Cannot send email - member has no email address.'))
            return

        try:
            template = self.env.ref('education_library.email_template_reservation_expired')
            template.send_mail(
                self.id,
                force_send=False,
                email_values={
                    'email_to': self.member_id.email,
                    'email_from': self.env.user.email_formatted or self.env.company.email
                }
            )
            self.message_post(body=_('Expiry notification email queued for %s') % self.member_id.email)
        except Exception as e:
            self.message_post(body=_('Failed to send expiry email: %s') % str(e))

    def _send_cancelled_notification(self):
        """Send notification that reservation was cancelled"""
        self.ensure_one()
        ICP = self.env['ir.config_parameter'].sudo()
        if not ICP.get_param('education_library.send_reservation_notifications', True):
            return

        if not self.member_id.email:
            self.message_post(body=_('Cannot send email - member has no email address.'))
            return

        try:
            template = self.env.ref('education_library.email_template_reservation_cancelled')
            template.send_mail(
                self.id,
                force_send=False,
                email_values={
                    'email_to': self.member_id.email,
                    'email_from': self.env.user.email_formatted or self.env.company.email
                }
            )
            self.message_post(body=_('Cancellation notification email queued for %s') % self.member_id.email)
        except Exception as e:
            self.message_post(body=_('Failed to send cancellation email: %s') % str(e))

    def _send_fulfilled_notification(self):
        """Send notification that book was issued"""
        self.ensure_one()
        ICP = self.env['ir.config_parameter'].sudo()
        if not ICP.get_param('education_library.send_reservation_notifications', True):
            return

        if not self.member_id.email:
            self.message_post(body=_('Cannot send email - member has no email address.'))
            return

        try:
            template = self.env.ref('education_library.email_template_reservation_fulfilled')
            template.send_mail(
                self.id,
                force_send=False,
                email_values={
                    'email_to': self.member_id.email,
                    'email_from': self.env.user.email_formatted or self.env.company.email
                }
            )
            self.message_post(body=_('Fulfillment notification email queued for %s') % self.member_id.email)
        except Exception as e:
            self.message_post(body=_('Failed to send fulfillment email: %s') % str(e))

    @api.model
    def _cron_check_expired_reservations(self):
        """Cron job to check and expire reservations"""
        today = fields.Date.today()
        expired_reservations = self.search([
            ('status', '=', 'available'),
            ('expiry_date', '<', today)
        ])

        for reservation in expired_reservations:
            try:
                reservation.action_mark_expired()
            except Exception as e:
                reservation.message_post(body=_('Failed to expire reservation: %s') % str(e))

    @api.model
    def _cron_send_expiry_reminders(self):
        """Cron job to send reminders for expiring reservations"""
        today = fields.Date.today()
        tomorrow = today + timedelta(days=1)
        expiring_reservations = self.search([
            ('status', '=', 'available'),
            ('expiry_date', '=', tomorrow)
        ])

        for reservation in expiring_reservations:
            try:
                reservation._send_expiry_reminder()
            except Exception as e:
                reservation.message_post(body=_('Failed to send reminder: %s    ') % str(e))