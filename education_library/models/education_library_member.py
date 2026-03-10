# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from datetime import timedelta


class EducationLibraryMember(models.Model):
    _name = 'education.library.member'
    _description = 'Library Member'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'membership_date desc'

    name = fields.Char(string='Name', compute='_compute_name', store=True)
    partner_id = fields.Many2one(comodel_name='res.partner', string='Partner', required=True, tracking=True)
    member_type = fields.Selection([
        ('student', 'Student'),
        ('faculty', 'Faculty'),
        ('staff', 'Staff'),
        ('external', 'External')
    ], string='Member Type', required=True, default='student', tracking=True)
    membership_date = fields.Date(string='Membership Date', tracking=True)
    expiry_date = fields.Date(string='Expiry Date', tracking=True)
    active = fields.Boolean(string='Active', default=True)
    is_expired = fields.Boolean(string='Expired', compute='_compute_is_expired')
    transaction_ids = fields.One2many(comodel_name='education.library.transaction', inverse_name='member_id',
                                      string='Transactions')
    transaction_count = fields.Integer(string='Transactions', compute='_compute_transaction_count')
    books_issued = fields.Integer(string='Books Issued', compute='_compute_books_issued')
    total_fines = fields.Float(string='Total Fines', compute='_compute_total_fines')
    email = fields.Char(related='partner_id.email', string='Email', readonly=True)
    phone = fields.Char(related='partner_id.phone', string='Phone', readonly=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('expired', 'Expired')
    ], string='Status', default='draft', compute='_compute_state', store=True, tracking=True)
    photo = fields.Binary(string='Image')

    # Reservation fields
    reservation_ids = fields.One2many('education.library.reservation', 'member_id', string='Reservations')
    reservation_count = fields.Integer(string='Reservations', compute='_compute_reservation_count')
    active_reservations_count = fields.Integer(string='Active Reservations', compute='_compute_active_reservations')
    unpaid_fines = fields.Float(string='Unpaid Fines', compute='_compute_unpaid_fines', store=True)
    invoice_ids = fields.One2many('account.move', 'library_member_id', string='Invoices')
    invoice_count = fields.Integer(string='Invoices', compute='_compute_invoice_count')

    @api.depends('partner_id.name')
    def _compute_name(self):
        for member in self:
            member.name = member.partner_id.name if member.partner_id else ''

    @api.depends('expiry_date', 'membership_date')
    def _compute_state(self):
        """Automatically compute state based on dates"""
        today = fields.Date.today()
        for member in self:
            if not member.membership_date:
                member.state = 'draft'
            elif member.expiry_date and today > member.expiry_date:
                member.state = 'expired'
            else:
                member.state = 'active'

    @api.depends('expiry_date')
    def _compute_is_expired(self):
        today = fields.Date.today()
        for member in self:
            member.is_expired = member.expiry_date and member.expiry_date < today

    @api.depends('transaction_ids')
    def _compute_transaction_count(self):
        for member in self:
            member.transaction_count = len(member.transaction_ids)

    @api.depends('transaction_ids.status')
    def _compute_books_issued(self):
        for member in self:
            member.books_issued = self.env['education.library.transaction'].search_count([
                ('member_id', '=', member.id),
                ('status', '=', 'issued')
            ])

    @api.depends('transaction_ids.fine_amount', 'transaction_ids.status')
    def _compute_total_fines(self):
        for member in self:
            transactions = member.transaction_ids.filtered(lambda t: t.status in ['issued', 'overdue', 'returned'])
            member.total_fines = sum(transactions.mapped('fine_amount'))

    @api.depends('reservation_ids')
    def _compute_reservation_count(self):
        for member in self:
            member.reservation_count = len(member.reservation_ids)

    @api.depends('reservation_ids.status')
    def _compute_active_reservations(self):
        for member in self:
            member.active_reservations_count = len(member.reservation_ids.filtered(
                lambda r: r.status in ['pending', 'available']
            ))

    @api.depends('transaction_ids.fine_amount', 'transaction_ids.status', 'invoice_ids.payment_state')
    def _compute_unpaid_fines(self):
        """Calculate total unpaid fines from transactions"""
        for member in self:
            # Get all fines from returned/overdue transactions
            total_fines = sum(member.transaction_ids.filtered(
                lambda t: t.status in ['returned', 'overdue']
            ).mapped('fine_amount'))

            # Subtract already invoiced and paid amounts
            paid_amount = sum(member.invoice_ids.filtered(
                lambda inv: inv.payment_state in ['paid', 'in_payment'] and
                            inv.state == 'posted'
            ).mapped('amount_total'))

            member.unpaid_fines = max(total_fines - paid_amount, 0.0)

    @api.depends('invoice_ids')
    def _compute_invoice_count(self):
        for member in self:
            member.invoice_count = len(member.invoice_ids)

    @api.constrains('expiry_date', 'membership_date')
    def _check_dates(self):
        for member in self:
            if member.expiry_date and member.membership_date:
                if member.expiry_date < member.membership_date:
                    raise ValidationError(_('Expiry date cannot be before membership date!'))

    def action_view_transactions(self):
        return {
            'name': _('Transactions'),
            'type': 'ir.actions.act_window',
            'res_model': 'education.library.transaction',
            'view_mode': 'list,form',
            'domain': [('member_id', '=', self.id)],
            'context': {'default_member_id': self.id}
        }

    def action_view_issued_transactions(self):
        return {
            'name': _('Transactions'),
            'type': 'ir.actions.act_window',
            'res_model': 'education.library.transaction',
            'view_mode': 'list,form',
            'domain': [
                ('member_id', '=', self.id),
                ('status', '=', 'issued'),
            ],
            'context': {'default_member_id': self.id},
        }

    def action_view_reservations(self):
        """View all reservations for this member"""
        return {
            'name': _('Reservations'),
            'type': 'ir.actions.act_window',
            'res_model': 'education.library.reservation',
            'view_mode': 'list,form',
            'domain': [('member_id', '=', self.id)],
            'context': {'default_member_id': self.id}
        }

    def action_register_member(self):
        """Register member - set membership and expiry dates"""
        ICP = self.env['ir.config_parameter'].sudo()

        for member in self:
            if member.state != 'draft':
                raise ValidationError(_('Only draft members can be registered!'))

            membership_date = fields.Date.today()

            # Get years from settings
            if member.member_type in ['faculty', 'staff']:
                years = int(ICP.get_param('education_library.faculty_membership_years', 2))
            else:
                years = int(ICP.get_param('education_library.student_membership_years', 1))

            expiry_date = membership_date + timedelta(days=365 * years)

            member.write({
                'membership_date': membership_date,
                'expiry_date': expiry_date
            })

            member.message_post(
                body=_('Member registered on %s. Membership valid until %s') % (membership_date, expiry_date)
            )

    def action_renew_membership(self):
        """Renew membership - extend expiry date"""
        ICP = self.env['ir.config_parameter'].sudo()

        for member in self:
            if member.state != 'expired':
                raise ValidationError(_('Only expired members can be renewed!'))

            membership_date = fields.Date.today()

            # Get years from settings
            if member.member_type in ['faculty', 'staff']:
                years = int(ICP.get_param('education_library.faculty_membership_years', 2))
            else:
                years = int(ICP.get_param('education_library.student_membership_years', 1))

            expiry_date = membership_date + timedelta(days=365 * years)

            member.write({
                'membership_date': membership_date,
                'expiry_date': expiry_date
            })

            member.message_post(
                body=_('Membership renewed on %s. New expiry date: %s') % (membership_date, expiry_date)
            )

    def action_create_fine_invoice(self):
        """Create invoice for unpaid fines"""
        self.ensure_one()
        ICP = self.env['ir.config_parameter'].sudo()

        if self.unpaid_fines <= 0:
            raise UserError(_('No unpaid fines to invoice!'))

        # Get fine product from settings
        product_id = int(ICP.get_param('education_library.fine_product_id', 0))
        if product_id:
            fine_product = self.env['product.product'].browse(product_id)
        else:
            fine_product = self.env.ref('education_library.product_library_fine', raise_if_not_found=False)

        if not fine_product:
            raise UserError(_('Library fine product not found! Please configure it in Library Settings.'))

        invoice_vals = {
            'move_type': 'out_invoice',
            'partner_id': self.partner_id.id,
            'library_member_id': self.id,
            'invoice_date': fields.Date.today(),
            'invoice_line_ids': [(0, 0, {
                'product_id': fine_product.id,
                'name': _('Library Late Return Fine - Member: %s') % self.name,
                'quantity': 1,
                'price_unit': self.unpaid_fines,
                'tax_ids': [(6, 0, [])],
            })]
        }

        invoice = self.env['account.move'].create(invoice_vals)

        self.message_post(
            body=_('Fine invoice created: %s for amount ₹%s') % (invoice.name, self.unpaid_fines)
        )

        return {
            'name': _('Fine Invoice'),
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'form',
            'res_id': invoice.id,
            'target': 'current',
        }

    def action_view_invoices(self):
        """View all invoices for this member"""
        return {
            'name': _('Invoices'),
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'list,form',
            'domain': [('library_member_id', '=', self.id)],
            'context': {'default_library_member_id': self.id}
        }
