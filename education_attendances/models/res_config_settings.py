from odoo import api, fields, models

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    # Attendance Summary Mode
    attendance_summary_enabled = fields.Boolean(
        string="Enable Summary Mode",
        default=True,
        config_parameter="edu_attendance.summary_enabled",
    )

    attendance_summary_mode = fields.Selection([
        ('daily', 'Daily Summary'),
        ('monthly', 'Monthly Summary'),
        ('annual', 'Annual Summary'),
        ('subject', 'Subject / Period-wise Summary'),
        ('term', 'Term / Semester-wise Summary'),
        ('overall', 'Overall Academic Year Summary'),
    ], string="Attendance Summary Mode",
    default='overall',
    config_parameter='edu_attendance.summary_mode')

    # Attendance Policy Configuration
    count_excused_as_present = fields.Boolean(
        string="Count Excused Absences as Present",
        default=True,
        config_parameter='edu_attendance.count_excused_as_present')
