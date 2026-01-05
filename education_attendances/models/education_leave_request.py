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
    _rec_name = 'student_id'

    student_id = fields.Many2one('res.partner', string='Name', domain=[('is_student', '=', True)])
    leave_format = fields.Selection([('full_day', 'Full Day'), ('half_day', 'Half Day')],required=True, string='Leave Format' )
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

    @api.depends("start_date", "end_date", "total_leave_days")
    def _compute_leave_day(self):
        """ Compute total leave days based on leave format.
            Full-day leave counts all days between start and end dates.
            Half-day leave counts as 0.5 day."""
        for record in self:
            if record.leave_format == 'full_day':
                if record.start_date and record.end_date:
                    total_day = record.end_date - record.start_date
                    record.total_leave_days = total_day.days + 1
            else:
                record.total_leave_days = 0.5 if record.end_date else 0

    @api.constrains('start_date', 'end_date')
    def _check_date_order(self):
        """Ensure end date is not before start date."""
        for rec in self:
            if rec.start_date and rec.end_date and rec.end_date < rec.start_date:
                raise ValidationError("End Date must be greater than or equal to Start Date.")

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
        """Prevent overlapping leave requests for the same student."""
        for rec in self:
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
        return super().write(vals)


