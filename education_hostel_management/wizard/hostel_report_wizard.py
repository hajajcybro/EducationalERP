from odoo import models, fields

class HostelReportWizard(models.TransientModel):
    _name = 'hostel.report.wizard'
    _description = 'Hostel Report Wizard'

    report_type = fields.Selection([
        ('occupancy', 'Occupancy per Hostel'),
        ('student', 'Student Room Assignment'),
        ('vacant', 'Vacant Rooms')
    ], required=True)

    student_id = fields.Many2one('res.partner', string="Student")
    hostel_id = fields.Many2one('education.hostel', string="Hostel")

    def action_print_report(self):

        data = {
            'report_type': self.report_type,
            'student_id': self.student_id.id,
            'hostel_id': self.hostel_id.id,
        }

        return self.env.ref('education_hostel_management.action_hostel_dynamic_report').report_action(self, data=data)