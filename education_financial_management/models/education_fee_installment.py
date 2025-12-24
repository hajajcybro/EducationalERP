# -*- coding: utf-8 -*-
from odoo import models, fields, api

class EduFeeInstallment(models.Model):
    _name = 'edu.fee.installment'
    _description = 'Fee Installment'
    _order = 'due_date'

    fee_plan_id = fields.Many2one(
        'edu.fee.plan',
        string='Fee Plan',
        required=True,
        ondelete='cascade'
    )

    name = fields.Char(
        string='Installment Name',
        required=True
    )

    due_date = fields.Date(
        string='Due Date',
        required=True
    )

    amount = fields.Monetary(
        string='Amount',
        required=True
    )

    currency_id = fields.Many2one(
        related='fee_plan_id.currency_id',
        store=True,
        readonly=True
    )

    penalty_rule_id = fields.Many2one(
        'edu.fee.penalty.rule',
        string='Penalty Rule'
    )
