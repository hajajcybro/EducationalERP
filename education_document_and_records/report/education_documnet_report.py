# -*- coding: UTF-8 -*-
from odoo import models, api

class DocumentReport(models.AbstractModel):
    _name = 'report.education_document_and_records.report_document_details'

    @api.model
    def _get_report_values(self, docids, data=None):
        print("get report values")
        query ="""SELECT rp.id AS student_id,rp.name AS student_name, dt.id AS document_type_id, dt.name 
                               AS document_type, dt.is_mandatory, d.issue_date, d.expiry_date,
                  d.version, d.state, CASE WHEN d.id IS NULL THEN 'Missing'  WHEN d.state != 'approved' THEN 'Pending'  
                  WHEN d.expiry_date IS NOT NULL AND d.expiry_date < CURRENT_DATE THEN 'Expired'
                  ELSE 'Valid'  END AS document_status FROM res_partner rp CROSS JOIN education_document_type dt LEFT JOIN LATERAL (
                  SELECT d1.* FROM education_document d1 WHERE d1.student_id = rp.id AND d1.document_type = dt.id
                  ORDER BY d1.version DESC LIMIT 1) d ON TRUE  WHERE rp.is_student = TRUE"""
        data = data or {}
        params = []

        if data.get('document_type_id'):
            query += " AND dt.id = %s" %data.get('document_type_id')


        if data.get('student_id'):
            query += " AND rp.id = %s" % data.get('student_id')

        if data.get('only_mandatory'):
            query += " AND dt.is_mandatory = TRUE"

        if data.get('expired_doc'):
            query += (" AND  d.expiry_date<=CURRENT_DATE AND d.expiry_date IS  NOT NULL")



        if data.get('report_type') == 'missing':
            query += " AND d.id IS NULL"

        if data.get('report_type') == 'pending':
            query += " AND d.id IS NOT NULL AND d.state != 'approved'"

        if data.get('only_expired'):
            query += " AND d.expiry_date < CURRENT_DATE"

        self.env.cr.execute(query,params)
        records = self.env.cr.dictfetchall()

        return {
            'doc_ids': docids,
            'doc_model': 'education.document',
            'docs': records,
            'data': data,
        }

