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
        # Send in-app notification to the student when refund request is rejected
        refund = self.refund_request_id
        partner = refund.student_id
        if partner:
            notif = self.env['edu.notification'].sudo().create({
                'name': 'Refund Request Rejected',
                'message': (
                    f'Your refund request of {refund.refund_amount} was rejected. '
                    f'Reason: {self.reason}'
                ),
                'recipient_ids': [(4, partner.id)],
                'module': 'financial',
                'notification_type': 'in_app',
                'status': 'draft',
            })
            notif.action_send()
