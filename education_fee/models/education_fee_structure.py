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
from odoo import api, fields, models


class EducationFeeStructure(models.Model):
    """Creates the model education fee structure"""
    _name = 'education.fee.structure'
    _description = 'Education Fee Structure'
    _rec_name = 'fee_structure_name'

    @api.depends('fee_type_ids.fee_amount')
    def _compute_amount_total(self):
        for rec in self:
            rec.amount_total = sum(line.fee_amount for line in rec.fee_type_ids)

    company_currency_id = fields.Many2one('res.currency',
                                          readonly=True, related_sudo=False,
                                          string="Currency",
                                          help="Related Currency")
    fee_structure_name = fields.Char(string='Name', required=True,
                                     help="Name of the Fee structure")
    fee_type_ids = fields.One2many('education.fee.structure.lines',
                                   'fee_structure_id', string='Fee Types',
                                   help="Types of the Fee structure")
    comment = fields.Text(string='Additional Information',
                          help="Additional information about the Fee structure")
    academic_year = fields.Many2one('education.academic.year',
                                    string='Academic Year', required=True,
                                    help="Academic year for the structure")
    expire = fields.Boolean(string='Expire', help="Is the structure expired")
    amount_total = fields.Float(string='Amount',
                                currency_field='company_currency_id',
                                required=True, compute='_compute_amount_total',
                                help="Total amount of the structure")
    category_id = fields.Many2one('education.fee.category', string='Category',
                                  help="Category for the structure",
                                  required=True,
                                  default=lambda self: self.env[
                                      'education.fee.category'].search([],
                                                                       limit=1),
                                  domain=[('fee_structure', '=', True)])


class EducationFeeStructureLines(models.Model):
    """Creates the model education fee structure lines"""
    _name = 'education.fee.structure.lines'
    _description = 'Education Fee Structure Lines'

    @api.onchange('fee_type')
    def _onchange_fee_type(self):
        return {
            'domain': {
                'fee_type': [
                    ('category_id', '=', self.fee_structure_id.category_id.id)]
            }
        }

    fee_type = fields.Many2one('education.fee.type', string='Fee',
                               required=True, help="Education Fee Type")
    fee_structure_id = fields.Many2one('education.fee.structure',
                                       string='Fee Structure',
                                       ondelete='cascade', index=True,
                                       help="Fee structure of the "
                                            "structure line")
    fee_amount = fields.Float(string='Amount', required=True,
                              related='fee_type.lst_price',
                              help="Amount of the fee")
    payment_type = fields.Selection([
        ('onetime', 'One Time'),
        ('permonth', 'Per Month'),
        ('peryear', 'Per Year'),
        ('sixmonth', '6 Months'),
        ('threemonth', '3 Months')
    ], string='Payment Type', related="fee_type.payment_type",
        help="Payment Type of the structure line")
    interval = fields.Char(related="fee_type.interval", string="Interval",
                           help="Interval in between payments")
    fee_description = fields.Text(string='Description',
                                  related='fee_type.description_sale',
                                  help="Description of the structure line")
