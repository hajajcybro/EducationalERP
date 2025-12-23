from odoo import models, fields, api, _
import io
import json
import xlsxwriter
from odoo.tools import json_default


class MissingDocumentReportWizard(models.TransientModel):
    _name = 'education.document.report.wizard'
    _description = 'Documents Report Wizard'

    report_type = fields.Selection([
        ('missing', 'Missing Documents'),
        ('pending', 'Pending Uploads'),
    ], string="Report Type")

    document_type_id = fields.Many2one(
        'education.document.type',
        string='Document Type',
        help='Filter by specific document type'
    )

    student_id = fields.Many2one(
        'res.partner',
        string='Student',
        domain=[('is_student', '=', True)]
    )

    only_mandatory = fields.Boolean(
        string="Only Mandatory Documents",
    )
    expired_doc =fields.Boolean(
        string="Only Expired Documents",
    )

    def action_generate_pdf_report(self):
        """Create button action for pdf report"""
        data = {
            'report_type': self.report_type,
            'document_type_id': self.document_type_id.id,
            'student_id': self.student_id.id,
            'only_mandatory': self.only_mandatory,
            'expired_doc': self.expired_doc,
        }
        print(data)
        return self.env.ref('education_document_and_records.action_document_report_information').report_action(None, data=data)


    def action_generate_xlsx_report(self):
        """Button action for generate xlxs report"""
        data = {
            'model_id': 'education.document.report.wizard',
            'report_type': self.report_type,
            'document_type_id': self.document_type_id.id,
            'student_id': self.student_id.id,
            'only_mandatory': self.only_mandatory,
            'expired_doc': self.expired_doc,
        }
        return {
            'type': 'ir.actions.report',
            'data': {'model': 'education.document.report.wizard',
                     'options': json.dumps(data, default=json_default),
                     'output_format': 'xlsx',
                     'report_name': 'Document Excel Report',
                     },
            'report_type': 'xlsx',
        }

    def get_xlsx_report(self, data, response):
        """Action for create XLXS report for student details"""
        print('abcd')

        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet('Vehicles')

        # Formats
        title = workbook.add_format({
            'bold': True, 'font_size': 18, 'align': 'center'
        })
        table_head = workbook.add_format({
            'bold': True, 'align': 'center', 'border': 1
        })
        text = workbook.add_format({
            'align': 'center', 'border': 1
        })
        date_fmt = workbook.add_format({
            'align': 'center',
            'border': 1,
            'num_format': 'yyyy-mm-dd'
        })

        # Column widths
        sheet.set_column('B:B', 18)
        sheet.set_column('C:C', 18)
        sheet.set_column('D:D', 20)
        sheet.set_column('E:E', 20)
        sheet.set_column('F:F', 22)
        sheet.set_column('G:G', 22)
        sheet.set_column('H:H', 21)

        # Table headers
        row = 1
        col = 0
        headers = [
            'Sl No',
            'Student',
            'Document Type',
            'Status',
            'Version',
            'Issue Date',
            'Expiry Date'
        ]

        for idx, header in enumerate(headers):
            sheet.write(row, col + idx, header, table_head)

        # SQL (same as PDF)

        query = """SELECT rp.id AS student_id,rp.name AS student_name, dt.id AS document_type_id, dt.name 
                               AS document_type, dt.is_mandatory, d.issue_date, d.expiry_date,
                  d.version, d.state, CASE WHEN d.id IS NULL THEN 'Missing'  WHEN d.state != 'approved' THEN 'Pending'  
                  WHEN d.expiry_date IS NOT NULL AND d.expiry_date < CURRENT_DATE THEN 'Expired'
                  ELSE 'Valid'  END AS document_status FROM res_partner rp CROSS JOIN education_document_type dt LEFT JOIN LATERAL (
                  SELECT d1.* FROM education_document d1 WHERE d1.student_id = rp.id AND d1.document_type = dt.id
                  ORDER BY d1.version DESC LIMIT 1) d ON TRUE  WHERE rp.is_student = TRUE"""

        if data.get('document_type_id'):
            query += " AND dt.id = %s" % data.get('document_type_id')

        if data.get('student_id'):
            query += " AND rp.id = %s" % data.get('student_id')

        if data.get('only_mandatory'):
            query += " AND dt.is_mandatory = TRUE"

        if data.get('expired_doc'):
            query += (" AND  d.expiry_date<=CURRENT_DATE AND d.expiry_date IS  NOT NULL ")

        if data.get('report_type') == 'missing':
            query += " AND d.id IS NULL"

        if data.get('report_type') == 'pending':
            query += " AND d.id IS NOT NULL AND d.state != 'approved'"

        if data.get('only_expired'):
            query += " AND d.expiry_date < CURRENT_DATE"

        self.env.cr.execute(query)
        records = self.env.cr.fetchall()

        # Write data
        row += 1
        sl_no = 1

        for rec in records:
            (
                student_id,
                student_name,
                document_type_id,
                document_type,
                is_mandatory,
                issue_date,
                expiry_date,
                version,
                state,
                document_status
            ) = rec

            sheet.write(row, 0, sl_no, text)
            sheet.write(row, 1, student_name or '-', text)
            sheet.write(row, 2, document_type or '-', text)
            sheet.write(row, 3, document_status or '-', text)
            sheet.write(row, 4, version or '-', text)
            sheet.write(row, 5, issue_date or '-', date_fmt)
            sheet.write(row, 6, expiry_date or '-', date_fmt)

            row += 1
            sl_no += 1

        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()

