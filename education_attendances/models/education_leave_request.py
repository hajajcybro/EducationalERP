# -*- coding: utf-8 -*-
from odoo import models, fields, api
import datetime
from odoo.exceptions import ValidationError
from odoo.exceptions import UserError

class EducationLeaveRequest(models.Model):
    """Manage student and faculty leave requests with approval workflow."""
    _name = 'education.leave.request'
    _description = 'Education Leave Request'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'reason'

    student_id = fields.Many2one('res.partner', string='Name', domain=[('position_role', '=', 'student')])
    leave_format = fields.Selection([
        ('full_day', 'Full Day'),
        ('half_day', 'Half Day'),
        ('both', 'Full Day + Hours'),
    ],required=True, string='Leave Format' )
    start_date = fields.Date(string='Start Date')
    end_date = fields.Date(string='End Date')
    total_leave_days = fields.Float(string='Total Days', compute='_compute_leave_day',store=True)
    reason = fields.Text(string='Reason',required=True)
    status = fields.Selection([
        ('draft', 'Draft'),
        ('to_approve', 'To Approve'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='draft', tracking=True)
    temporary = fields.Date()
    teacher_id = fields.Many2one(
        'hr.employee',
        string='Teacher',
        domain=[('role', '=', 'teacher')],
    )
    session = fields.Selection([
        ('forenoon', 'Forenoon'),
        ('afternoon', 'Afternoon'),
    ], string="Session")

    half_day_date = fields.Date(string='Half-Day Date')
    leave_days = fields.Integer(
        string="No. of Days"
    )

    @api.onchange('leave_format', 'start_date', 'end_date')
    def _onchange_half_day_dates(self):
        """Automatically align end date with start date for half-day leave.
           When the leave format is set to 'half_day', this ensures the leave
           duration is restricted to a single day by setting the end date
           equal to the start date.
           """
        if self.leave_format == 'half_day' and self.start_date:
            self.end_date = self.start_date

    @api.depends('start_date','end_date','leave_format','leave_days',)
    def _compute_leave_day(self):
        """Compute total leave days based on leave format."""
        for rec in self:
            total = 0.0
            if rec.leave_format == 'full_day':
                if rec.start_date and rec.end_date:
                    total = (rec.end_date - rec.start_date).days + 1
            elif rec.leave_format == 'half_day':
                total = 0.5
            elif rec.leave_format == 'both':
                if rec.leave_days:
                    total = rec.leave_days + 0.5
            rec.total_leave_days = total

    @api.constrains('total_leave_days')
    def _check_total_leave_days(self):
        """Ensure total leave days is greater than zero."""
        for record in self:
            if record.total_leave_days <= 0:
                raise ValidationError("Total leave days must be greater than zero, Please check the dates")

    def action_submit(self):
        """Move the request to 'Submitted' state."""
        for rec in self:
            rec.status = 'to_approve'

    def action_approve(self):
            """Approve the leave request and set approver."""
            for rec in self:
                rec.status = 'approved'

    def action_reject(self):
            """Reject the leave request."""
            for rec in self:
                rec.status = 'rejected'

    def action_cancel(self):
            """Cancel the leave request."""
            for rec in self:
                rec.status = 'cancelled'

    @api.constrains('student_id', 'start_date', 'end_date')
    def _check_overlapping_leave(self):
        """Validate date order and prevent overlapping leave requests."""
        for rec in self:
            if rec.start_date and rec.end_date and rec.end_date < rec.start_date:
                raise ValidationError(
                    "End Date must be greater than or equal to Start Date."
                )
            overlapping = self.search([
                ('id', '!=', rec.id),
                ('student_id', '=', rec.student_id.id),
                ('status', 'not in', ['cancelled', 'rejected']),
                ('start_date', '<=', rec.end_date),
                ('end_date', '>=', rec.start_date),
            ], limit=1)
            if overlapping:
                raise ValidationError("An existing leave already covers the selected dates.")

    def write(self, vals):
        """ Prevent modification of approved leave records.
            Once a leave request is approved, it cannot be edited to
            ensure data integrity and approval consistency."""
        for rec in self:
            if rec.status == 'approved':
                raise UserError("Approved leave cannot be modified.")
            # Trigger notification when leave status changes to 'approved' or 'rejected'
            if 'status' in vals and vals['status'] in ['approved', 'rejected']:
                for rec in self:
                    if rec.student_id:
                        status_text = "Approved" if vals['status'] == 'approved' else "Rejected"

                        # We are calling 'edu.notification' from the Notification module
                        notif = self.env['edu.notification'].sudo().create({
                            'name': f'Leave {status_text}',
                            'message': f'Your leave request for {rec.start_date} was {status_text.lower()}.',
                            'recipient_ids': [(4, rec.student_id.id)],
                            'module': 'attendance',
                            'notification_type': 'in_app',
                            'status': 'draft'
                        })
                        notif.action_send()
        return super().write(vals)

    @api.onchange('start_date', 'leave_days')
    def _onchange_leave_days(self):
        for rec in self:
            if rec.start_date and rec.leave_days:
                rec.end_date = rec.start_date + datetime.timedelta(
                    days=rec.leave_days - 1
                )



