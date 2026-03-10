from odoo import models


class AcademicYear(models.Model):
    _inherit = 'education.academic.year'   # model from education_core

    def action_set_closed(self):
        res = super().action_set_closed()

        for rec in self:
            self.env['education.audit.log'].sudo().create({
                'user_id': self.env.user.id,
                'action_type': 'approval',
                'model_name': rec._name,
                'record_id': rec.id,
                'description': f"Academic Year '{rec.name}' closed.",
                'severity': 'info',
                'source': 'internal',
            })

        return res