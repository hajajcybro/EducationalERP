# -*- coding: utf-8 -*-
from odoo import models, fields, api,_
from odoo.exceptions import UserError



class TransportDelayWizard(models.TransientModel):
    _name = 'transport.delay.wizard'
    _description = 'Transport Delay Notification Wizard'

    route_id = fields.Many2one('education.transport.route', required=True,)
    delay_minutes = fields.Integer(required=True)
    delay_reason = fields.Text(required=True)

    def action_send_notifications(self):
        """Send delay notification email to all parents"""
        assignments = self.env['education.transport.assignment'].search([
            ('route_id', '=', self.route_id.id),
            ('active', '=', True)
        ])
        partner_ids = []
        for assign in assignments:
            parent_email = assign.student_id.parent_email
            if parent_email:
                partner = self.env['res.partner'].sudo().search(
                    [('email', '=', parent_email)], limit=1
                )
                if not partner:
                    partner = self.env['res.partner'].sudo().create({
                        'name': f"Parent of {assign.student_id.name}",
                        'email': parent_email,
                    })
                partner_ids.append(partner.id)
        if not partner_ids:
            raise UserError(_('No parent email addresses are configured.'))
        # Create and send via edu.notification
        notification = self.env['edu.notification'].sudo().create({
            'name': f'Transport Delay Alert – {self.route_id.name}',
            'message': (
                f"Dear Parent,\n\n"
                f"Please be informed that the school transport route "
                f"{self.route_id.name} is delayed.\n\n"
                f"Expected Delay: {self.delay_minutes} minutes\n"
                f"Reason: {self.delay_reason}\n\n"
                f"Thank you for your cooperation.\n\n"
                f"Regards,\nTransport Administration"
            ),
            'notification_type': 'email',
            'module': 'transport',
            'recipient_ids': [(6, 0, partner_ids)],
            'scheduled_date': fields.Datetime.now(),
        })
        notification.action_send()
        # print(assignments)
        # Mail = self.env['mail.mail']
        # email_sent = False
        #
        # for assign in assignments:
        #     parent = assign.student_id.parent_email
        #     if parent:
        #         print(parent)
        #         email_sent = True
        #         Mail.create({
        #             'subject': f'Transport Delay Alert – {self.route_id.name}',
        #             'email_to': parent,
        #             'body_html': f"""
        #                        <p>Dear Parent,</p>
        #                        <p>Please be informed that the school transport route
        #                        <b>{self.route_id.name}</b> is delayed.</p>
        #                        <p>
        #                            <b>Expected Delay:</b> {self.delay_minutes} minutes<br/>
        #                            <b>Reason:</b> {self.delay_reason}
        #                        </p>
        #                        <p>Thank you for your cooperation.</p>
        #                        <p>
        #                            Regards,<br/>
        #                            <b>Transport Administration</b>
        #                        </p>
        #                    """
        #         }).send()
        #
        # if not email_sent:
        #     print('no email')
        #     raise UserError(
        #         _('No parent email addresses are configured.')
        #     )

        return {'type': 'ir.actions.act_window_close'}





