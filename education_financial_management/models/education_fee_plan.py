# -*- coding: utf-8 -*-
from odoo import models, fields, api


class EduFeePlan(models.Model):
    _name = 'education.fee.plan'
    _description = 'Fee Plan'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'academic_year_id desc, name'

    name = fields.Char(
        string='Fee Plan Name',
        required=True,
        tracking=True,
        help='Name of the fee plan.'
    )

    program_id = fields.Many2one(
        'edu.program',
        string='Program',
        tracking=True
    )

    academic_year_id = fields.Many2one(
        'edu.academic.year',
        string='Academic Year',
        tracking=True
    )

    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        required=True,
        default=lambda self: self.env.company.currency_id
    )

    installment_ids = fields.One2many(
        'edu.fee.installment',
        'fee_plan_id',
        string='Installments'
    )

    notes = fields.Text(string='Notes')

    active = fields.Boolean(default=True)
