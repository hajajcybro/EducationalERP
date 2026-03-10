# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class EducationLibraryBook(models.Model):
    _name = 'education.library.book'
    _description = 'Library Book'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'title'

    name = fields.Char(string='Name', compute='_compute_name', store=True)
    isbn = fields.Char(string='ISBN')
    title = fields.Char(string='Title', required=True, tracking=True)
    authors = fields.Char(string='Authors', tracking=True)
    publisher = fields.Char(string='Publisher')
    publish_date = fields.Date(string='Publish Date')
    edition = fields.Char(string='Edition')
    category_id = fields.Many2one(comodel_name='education.library.category', string='Category', tracking=True)
    barcode = fields.Char(string='Barcode', copy=False)
    copies_total = fields.Integer(string='Total Copies', default=1, required=True)
    copies_available = fields.Integer(string='Available', compute='_compute_copies', store=True)
    copies_issued = fields.Integer(string='Issued', compute='_compute_copies', store=True)
    state = fields.Selection([
        ('available', 'Available'),
        ('issued', 'Issued'),
        ('lost', 'Lost'),
        ('damaged', 'Damaged'),
        ('archived', 'Archived')
    ], string='Status', default='available', required=True, tracking=True)
    description = fields.Text(string='Description')
    active = fields.Boolean(string='Active', default=True)
    transaction_ids = fields.One2many(comodel_name='education.library.transaction', inverse_name='book_id',
                                      string='Transactions')
    transaction_count = fields.Integer(string='Transactions', compute='_compute_transaction_count')
    photo = fields.Binary(string='Image')

    reservation_ids = fields.One2many('education.library.reservation', 'book_id', string='Reservations')
    reservation_count = fields.Integer(string='Reservations', compute='_compute_reservation_count')
    pending_reservations = fields.Integer(string='Pending Reservations', compute='_compute_pending_reservations')
    has_reservations = fields.Boolean(string='Has Reservations', compute='_compute_has_reservations')

    @api.depends('title')
    def _compute_name(self):
        for book in self:
            book.name = book.title

    @api.depends('transaction_ids.status', 'copies_total')
    def _compute_copies(self):
        for book in self:
            # Count only 'issued' and 'overdue' transactions as currently issued
            issued = self.env['education.library.transaction'].search_count([
                ('book_id', '=', book.id),
                ('status', 'in', ['issued', 'overdue'])
            ])
            book.copies_issued = issued
            book.copies_available = book.copies_total - issued

    @api.depends('transaction_ids')
    def _compute_transaction_count(self):
        for book in self:
            book.transaction_count = len(book.transaction_ids)

    @api.depends('reservation_ids')
    def _compute_reservation_count(self):
        for book in self:
            book.reservation_count = len(book.reservation_ids)

    @api.depends('reservation_ids.status')
    def _compute_pending_reservations(self):
        for book in self:
            book.pending_reservations = len(book.reservation_ids.filtered(
                lambda r: r.status == 'pending'
            ))

    @api.depends('pending_reservations')
    def _compute_has_reservations(self):
        for book in self:
            book.has_reservations = book.pending_reservations > 0

    @api.constrains('copies_total')
    def _check_copies_total(self):
        for book in self:
            if book.copies_total < 0:
                raise ValidationError(_('Total copies cannot be negative!'))
            if book.copies_total < book.copies_issued:
                raise ValidationError(
                    _('Cannot set total copies to %s. Currently %s copies are issued!') % (book.copies_total,
                                                                                           book.copies_issued))

    def write(self, vals):
        """Override write to auto-update state when copies change"""
        res = super(EducationLibraryBook, self).write(vals)
        if 'copies_total' in vals:
            for book in self:
                book._auto_update_state()

        return res

    def _auto_update_state(self):
        """Automatically update book state based on availability"""
        self.ensure_one()

        if self.state in ['damaged', 'archived']:
            return

        self._compute_copies()

        if self.copies_total == 0:
            if self.state != 'lost':
                self.state = 'lost'
                self.message_post(body=_('Book state automatically changed to Lost (no copies available)'))
        elif self.copies_available == 0 and self.copies_issued > 0:
            if self.state != 'issued':
                self.state = 'issued'
        elif self.copies_available > 0:
            if self.state in ['lost', 'issued']:
                self.state = 'available'
                self.message_post(body=_('Book state automatically changed to Available (copies added/returned)'))

    def action_view_transactions(self):
        return {
            'name': _('Transactions'),
            'type': 'ir.actions.act_window',
            'res_model': 'education.library.transaction',
            'view_mode': 'list,form',
            'domain': [('book_id', '=', self.id)],
            'context': {'default_book_id': self.id, 'create': False}
        }

    def action_view_reservations(self):
        """View all reservations for this book"""
        return {
            'name': _('Reservations'),
            'type': 'ir.actions.act_window',
            'res_model': 'education.library.reservation',
            'view_mode': 'list,form',
            'domain': [('book_id', '=', self.id)],
            'context': {'default_book_id': self.id}
        }

    def action_view_current_reservations(self):
        """View all reservations for this book"""
        return {
            'name': _('Reservations'),
            'type': 'ir.actions.act_window',
            'res_model': 'education.library.reservation',
            'view_mode': 'list,form',
            'domain': [
                ('book_id', '=', self.id),
                ('status', 'in', ['pending', 'available']),
            ],
            'context': {'default_book_id': self.id}
        }

    def action_reserve_book(self):
        """Quick action to reserve this book"""
        self.ensure_one()
        if self.copies_available > 0:
            raise ValidationError(_('Book has available copies. Please issue directly instead of reserving.'))

        return {
            'name': _('Reserve Book'),
            'type': 'ir.actions.act_window',
            'res_model': 'education.library.reservation',
            'view_mode': 'form',
            'context': {
                'default_book_id': self.id,
            },
            'target': 'new'
        }

    def action_mark_available(self):
        """Manual button to mark book as available"""
        for book in self:
            if book.copies_available > 0:
                book.state = 'available'
                book.message_post(body=_('Book manually marked as Available'))
            else:
                raise ValidationError(_('Cannot mark as available. No copies are available!'))

    def action_mark_damaged(self):
        """Manual button to mark book as damaged"""
        for book in self:
            book.state = 'damaged'
            book.message_post(body=_('Book marked as Damaged'))

    def _allocate_to_next_reservation(self):
        """Allocate book to next person in reservation queue"""
        self.ensure_one()

        next_reservation = self.env['education.library.reservation'].search([
            ('book_id', '=', self.id),
            ('status', '=', 'pending')
        ], order='priority, reservation_date', limit=1)

        if next_reservation:
            next_reservation.action_mark_available(expiry_hours=48)
            return next_reservation
        return False