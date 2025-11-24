# -*- coding: utf-8 -*-
from odoo import models, fields


class EducationAttendanceLine(models.Model):
    _name = 'education.attendance.line'
    _description = 'Attendance Line'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'student_id'


    attendance_id = fields.Many2one('education.attendance',
                                    string="Attendance", ondelete='cascade')
    student_id = fields.Many2one('education.enrollment',
                                 string="Student", required=True)
    status = fields.Selection([
        ('present', 'Present'),
        ('absent', 'Absent'),
        ('late', 'Late'),
        ('leave', 'Leave')
    ], string="Status", required=True,)
    remarks = fields.Char(string="Remarks")




