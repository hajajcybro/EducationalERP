from odoo import api, fields, models

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    # Attendance Summary Mode
    attendance_summary_enabled = fields.Boolean(
        string="Attendance Summary Mode",
        config_parameter="education_attendances.summary_enabled",
    )

    attendance_summary_mode = fields.Selection([
        ('daily', 'Daily Summary'),
        ('monthly', 'Monthly Summary'),
        ('annual', 'Annual Summary'),
        ('subject', 'Subject / Period-wise Summary'),
    ],
    default='daily',
    config_parameter='education_attendances.summary_mode')

    # Attendance Policy Configuration
    count_excused_as_present = fields.Boolean(
        string="Count Excused Leave as Present",
        config_parameter='education_attendances.count_excused_as_present')

    # AUTO RECALCULATE WHEN SETTINGS CHANGE
    def set_values(self):
        print('set values')
        old_mode = self.env['ir.config_parameter'].sudo().get_param(
            'education_attendances.summary_mode'
        )
        super().set_values()
        new_mode = self.env['ir.config_parameter'].sudo().get_param(
            'education_attendances.summary_mode'
        )
        # Mode changed - Recalculate summary
        if old_mode != new_mode:
            print('new')
            self.env['education.attendance.summary'].action_recalculate_all()
        return True

