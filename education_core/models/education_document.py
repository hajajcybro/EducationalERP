# -*- coding: utf-8 -*-
from odoo import api, fields, models,_
from odoo.exceptions import ValidationError


class EducationDocument(models.Model):
    """ This model represents education.document."""
    _name = 'education.document'
    _description = 'Education Document'
    _inherit = ['mail.thread']
    _rec_name = 'student_id'

    student_id = fields.Many2one(
        'education.student.student',
        string='Student',
        required=True,
        ondelete='cascade',
    )
    admission_no = fields.Char(
        string='Admission No',
        compute='_compute_admission_no',
        store=True,
        readonly=True
    )
    document_type = fields.Selection([
        ('birth_certificate', 'Birth Certificate'),
        ('transfer_certificate', 'Transfer Certificate'),
        ('mark_sheet', 'Mark Sheet'),
        ('id_proof', 'ID Proof'),
        ('photo', 'Photo'),
        ('medical_certificate', 'Medical Certificate'),
        ('income_certificate', 'Income Certificate'),
        ('other', 'Other'),
    ], string='Document Type', required=True)

    reference = fields.Char(string='Reference Code')
    issue_date = fields.Date(
        string='Issue Date',
        default=fields.Date.today,
        readonly=True,
    )
    attachment = fields.Binary(string='Attachment', required=True)
    file_name = fields.Char(string='File Name')
    active = fields.Boolean(default=True)
    notes = fields.Text(string='Internal Notes')

    @api.depends('student_id')
    def _compute_admission_no(self):
        """Auto-update admission no based on selected student"""
        for rec in self:
            rec.admission_no = rec.student_id.admission_no if rec.student_id else False

    @api.constrains('student_id', 'document_type')
    def _check_unique_student_document(self):
        for rec in self:
            if rec.student_id and rec.document_type:
                duplicate = self.search([
                    ('id', '!=', rec.id),
                    ('student_id', '=', rec.student_id.id),
                    ('document_type', '=', rec.document_type)
                ], limit=1)
                if duplicate:
                    raise ValidationError(
                        f"The student '{rec.student_id.name}' already has a document of type '{rec.document_type}'."
                    )



