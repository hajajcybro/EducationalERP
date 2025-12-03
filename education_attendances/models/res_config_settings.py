from odoo import api, fields, models

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    # Attendance Summary Mode
    track_attendance_enabled = fields.Boolean(
        string="Attendance Tracking Mode",
        config_parameter="education_attendances.track_enabled",
    )
    attendance_tracking_mode = fields.Selection([
        ('day', 'Day-wise'),
        ('period', 'Period-wise'),
        ('half_day', 'Half-day'),
        ('hourly', 'Hourly')
    ], default='period', config_parameter='education_attendances.tracking_mode')

    minimum_attendance_enabled = fields.Boolean(
        string="Minimum Attendance Percentage",
        config_parameter="education_attendances.attendance_enabled",
    )
    minimum_attendance_percentage = fields.Float(
        config_parameter='education_attendances.minimum_attendance',
        default=75.0)


    # Attendance Policy Configuration
    count_excused_as_present = fields.Boolean(
        string="Count Excused Leave as Present",
        config_parameter='education_attendances.count_excused_as_present')

