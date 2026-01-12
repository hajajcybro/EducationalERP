# -*- coding: utf-8 -*-
from email.policy import default

from odoo import models, fields

class HrEmployee(models.Model):
    """Extend partner to add position role"""
    _inherit = 'hr.employee'

    role = fields.Selection(
        selection=[('teacher', 'Teacher'), ('staff', 'Office Staff'),('driver','Driver'),('other','Other')],
        string='Position',
    )
    other_role = fields.Char('Other Role')

    def unlink(self):
        """ Override unlink to log audit details when deleting staff records.
        Tracks deletion of Teacher and Driver records by capturing key
        employee details such as role, department, job position, and
        contact information for audit purposes."""
        for rec in self:
            if rec.role in ('teacher', 'driver'):
                old_data = {
                    'Employee Name': rec.name,
                    'Role': rec.role,
                    'Department': rec.department_id.display_name if rec.department_id else None,
                    'Job Position': rec.job_id.display_name if rec.job_id else None,
                    'Work Email': rec.work_email,
                    'Work Phone': rec.work_phone,
                }
                self.env['education.audit.log'].sudo().create({
                    'user_id': self.env.user.id,
                    'action_type': 'delete',
                    'model_name': rec._name,
                    'record_id': rec.id,
                    'description': f'{rec.role.capitalize()} record deleted',
                    'old_values': old_data,
                })
        return super().unlink()
