# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Arjun S (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
import datetime
from odoo import api, fields, models


class AccountMove(models.Model):
    """Inherited the model account.move and added extra functionalities and
    fields for the working of the module"""
    _inherit = 'account.move'

    @api.onchange('fee_structure')
    def _onchange_fee_structure(self):
        """Set default fee lines based on selected fee structure"""
        lines = []
        for item in self:
            for line in item.fee_structure.fee_type_ids:
                name = line.fee_type.product_id.description_sale
                if not name:
                    name = line.fee_type.product_id.name
                fee_line = {
                    'price_unit': line.fee_amount,
                    'quantity': 1.00,
                    'product_id': line.fee_type.product_id,
                    'name': name,
                    'account_id': item.journal_id.default_account_id
                }
                lines.append((0, 0, fee_line))
            item.invoice_line_ids = lines

    @api.onchange('student_id', 'fee_category_id', 'payed_from_date',
                  'payed_to_date')
    def _onchange_partner_details(self):
        """Student_id is inherited from res_partner. Set partner_id from
        student_id """
        self.ensure_one()
        lines = []
        for item in self:
            item.invoice_line_ids = lines
            item.partner_id = item.student_id.partner_id
            item.class_division_id = item.student_id.class_id
            date_today = datetime.date.today()
            company = self.env.user.company_id
            from_date = item.payed_from_date
            to_date = item.payed_to_date
            if not from_date:
                from_date = company.compute_fiscalyear_dates(date_today)[
                    'date_from']
            if not to_date:
                to_date = date_today
            if item.partner_id and item.fee_category_id:
                invoice_ids = self.env['account.move'].search([
                    ('partner_id', '=', item.partner_id.id),
                    ('invoice_date', '>=', from_date),
                    ('invoice_date', '<=', to_date),
                    ('fee_category_id', '=', item.fee_category_id.id)])
                invoice_line_list = []
                for invoice in invoice_ids:
                    for line in invoice.invoice_line_ids:
                        fee_line = {
                            'price_unit': line.price_unit,
                            'quantity': line.quantity,
                            'product_id': line.product_id,
                            'price_subtotal': line.price_subtotal,
                            'tax_ids': line.tax_ids,
                            'discount': line.discount,
                            'receipt_no': line.move_name,
                            'date': line.move_id.invoice_date,
                        }
                        invoice_line_list.append((0, 0, fee_line))
                item.payed_line_ids = invoice_line_list

    @api.onchange('fee_category_id')
    def _onchange_fee_category_id(self):
        """ Set domain for fee structure based on category"""
        if self.fee_category_id:
            line = self.fee_category_id.journal_id
            self.journal_id = line
        self.invoice_line_ids = None
        return {
            'domain': {
                'fee_structure': [('category_id', '=', self.fee_category_id.id)]
            }
        }

    student_id = fields.Many2one('education.student', string='Admission No',
                                 help='Student Corresponding to this invoice')
    student_name = fields.Char(string='Name',
                               related='student_id.partner_id.name', store=True,
                               help="Name of student")
    class_division_id = fields.Many2one('education.class.division',
                                        string='Class', help="Division of "
                                                             "class")
    fee_structure = fields.Many2one('education.fee.structure',
                                    string='Fee Structure',
                                    help="Structure of Fees")
    is_fee = fields.Boolean(string='Is Fee', help="Weather the invoice is fee")
    fee_category_id = fields.Many2one('education.fee.category',
                                      string='Category', help="Fee Category")
    is_fee_structure = fields.Boolean(string='Have a fee structure?',
                                      related='fee_category_id.fee_structure',
                                      help="True when is a fee structure")
    payed_line_ids = fields.One2many('payed.lines', 'partner_id',
                                     string='Payments Done',
                                     readonly=True, store=False,
                                     help="Line which will show the paid ones")
    payed_from_date = fields.Date(string='From Date', help="Date from")
    payed_to_date = fields.Date(string='To Date', help="Date to")
    account_id = fields.Many2one('account.account', string='Account',
                                 index=True, ondelete="cascade",
                                 domain="[('deprecated', '=', False),"
                                        " ('company_id', '=', 'company_id')"
                                        ",('is_off_balance', '=', False)]",
                                 check_company=True,
                                 tracking=True, help="Account related")

    @api.model
    def create(self, vals):
        """ Adding two field to invoice. is_fee use to display fee items only
        in fee tree view"""
        partner = self.env['res.partner'].browse(vals.get('partner_id'))
        if vals.get('fee_category_id'):
            vals.update({
                'is_fee': True,
                'student_name': partner.name
            })
        res = super(AccountMove, self).create(vals)
        return res


class AccountMoveLine(models.Model):
    """Inherit the model account.move.line to add extra fields and
    functionalities"""
    _inherit = 'account.move.line'

    manual = fields.Boolean(default=True, string="Is Manual",
                            help="Becomes True if manual move")

    @api.onchange('product_id')
    def _onchange_product_id(self):
        """Set domain for invoice lines depend on selected category"""
        if self.move_id.fee_category_id:
            fee_types = self.env['education.fee.type'].search(
                [('category_id', '=', self.move_id.fee_category_id.id)])
            fee_list = [fee.product_id.id for fee in fee_types]
            vals = {
                'domain': {
                    'product_id': [('id', 'in', tuple(fee_list))]
                }
            }
            return vals


class PayedLines(models.Model):
    """Creates the payed lines"""
    _name = 'payed.lines'
    _inherit = 'account.move.line'

    date = fields.Date(string='Date', readonly=True,
                       help="Date when payed the fees")
    receipt_no = fields.Char(string='Receipt No',
                             help="Receipt number of the payed lines")
