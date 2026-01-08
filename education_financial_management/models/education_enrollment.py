# -*- coding: utf-8 -*-
from odoo import api, fields, models

class EducationEnrollment(models.Model):
    _inherit = 'education.enrollment'

    def action_view_fee_invoices(self):
        print(self)
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Fee Invoices',
            'res_model': 'education.fee.invoice',
            'view_mode': 'form,list',
            'domain': [
                ('enrollment_id', '=', self.id),
            ],
            'context': {
                'default_student_id': self.student_id.partner_id.id,
                'default_admission_no': self.admission_no,
                'default_enrollment_id': self.id,
            }
        }