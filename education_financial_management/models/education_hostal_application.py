from odoo import models, fields

class EducationHostelApplication(models.Model):
    _inherit = 'education.hostel.application'

    invoice_count = fields.Integer(
        string='Invoices'
    )

    def action_view_invoices(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Invoices',
            'res_model': 'education.fee.invoice',
            'view_mode': 'list,form',
            'domain': [('hostel_application_id', '=', self.id)],
        }
