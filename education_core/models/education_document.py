# -*- coding: utf-8 -*-
from odoo import api, fields, models,_
from odoo.exceptions import ValidationError


class EducationDocument(models.Model):
    """ This model represents education.academic.year."""
    _name = 'education.document'
    _description = 'Education Document'
    _inherit = ['mail.thread']
    _rec_name = 'student_id'

    student_id = fields.Many2one(
        'education.student.student',
        string='Student',
        required=True,
    )
    document_type = fields.Selection([
        ('birth_certificate', 'Birth Certificate'),
        ('transfer_certificate', 'Transfer Certificate'),
        ('mark_sheet', 'Mark Sheet'),
        ('id_proof', 'ID Proof'),
        ('photo', 'Photo'),
        ('medical_certificate', 'Medical Certificate'),
        ('caste_certificate', 'Caste Certificate'),
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


