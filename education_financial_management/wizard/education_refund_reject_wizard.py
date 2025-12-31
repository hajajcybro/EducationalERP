# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class EducationRefundRejectWizard(models.TransientModel):
    _name = 'education.refund.reject.wizard'
    _description = 'Reject Refund Request Wizard'

    refund_request_id = fields.Many2one(
        'education.refund.request',
        string='Refund Request',
        required=True,
        readonly=True
    )

    reason = fields.Text(
        string='Rejection Reason',
        required=True
    )

    def action_submit(self):
        """
        Submit rejection reason and mark refund request as rejected.
        """
        self.ensure_one()
        self.refund_request_id.write({
            'state': 'rejected',
            'rejection_reason': self.reason,
        })
