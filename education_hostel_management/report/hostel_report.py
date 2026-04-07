from odoo import models

class HostelDynamicReport(models.AbstractModel):
    _name = 'report.education_hostel_management.report_hostel_dynamic'

    def _get_report_values(self, docids, data=None):
        data = data or {}
        report_type = data.get('report_type')
        student_id = data.get('student_id')
        hostel_id = data.get('hostel_id')
        docs = []
        if report_type == 'occupancy':
            domain = []
            if hostel_id:
                domain.append(('id', '=', hostel_id))
            docs = self.env['education.hostel'].search(domain)
        elif report_type == 'student':
            domain = []
            if student_id:
                domain.append(('hostel_application_id.student_id', '=', student_id))
            if hostel_id:
                domain.append(('hostel_id', '=', hostel_id))
            docs = self.env['education.hostel.room.allocation'].search(domain)

        elif report_type == 'vacant':
            domain = [('vacancy', '>', 0)]
            if hostel_id:
                domain.append(('hostel_id', '=', hostel_id))
            docs = self.env['education.hostel.room'].search(domain)
        return {
            'doc_ids': docids,
            'doc_model': 'education.hostel',
            'docs': docs,
            'data': data,
        }