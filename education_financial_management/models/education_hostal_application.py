from odoo import models, fields

class EducationHostelApplication(models.Model):
    _inherit = 'education.hostel.application'

    invoice_count = fields.Integer(
        string='Invoices'
    )
    def action_view_invoices(self):
        """
        Open the related hostel fee invoice for the student if it exists;
        otherwise, open a new fee invoice form with hostel defaults prefilled.
        """
        self.ensure_one()
        FeeInvoice = self.env['education.fee.invoice']
        invoice = FeeInvoice.search([
            ('student_id', '=', self.student_id.id),
            ('admission_no', '=', self.student_id.admission_no),
            ('payment_type', '=', 'hostel'),
        ], limit=1)
        if invoice:
            return {
                'type': 'ir.actions.act_window',
                'name': 'Hostel Fee Invoice',
                'res_model': 'education.fee.invoice',
                'view_mode': 'form',
                'res_id': invoice.id,
                'target': 'current',
            }
        return {
            'type': 'ir.actions.act_window',
            'name': 'Invoices',
            'res_model': 'education.fee.invoice',
            'view_mode': 'form',
            'context': {
                'default_student_id': self.student_id.id,
                'default_payment_type': 'hostel',
                'default_hostel_application_id': self.id,
            }
        }
