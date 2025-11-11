# -*- coding: utf-8 -*-
from odoo import api, fields, models,_
from odoo.exceptions import ValidationError


class EducationDocument(models.Model):
    """ This model represents education.document."""
    _name = 'education.document'
    _description = 'Education Document'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'student_id'

    student_id = fields.Many2one(
        'res.partner',
        string='Student',
        required=True,
        ondelete='cascade',
        domain=[('position_role', '=', 'student')]
    )
    admission_no = fields.Char(
        string='Admission No',
        compute='_compute_admission_no',
        store=True,
    )
    document_type = fields.Many2one('education.document.type',
                                    string='Document Type', required=True
                                    )

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
    def _check_document_limit(self):
        """Restrict number of uploads of same document type per student."""
        for rec in self:
            existing_docs = self.search([
                ('id', '!=', rec.id),
                ('student_id', '=', rec.student_id.id),
                ('document_type', '=', rec.document_type.id)
            ])

            limit = rec.document_type.limit

            if len(existing_docs) >= limit:
                raise ValidationError(_(
                    "The student '%s' has already uploaded %d '%s' document(s). "
                    "The allowed limit is %d."
                ) % (
                    rec.student_id.name,
                    len(existing_docs),
                    rec.document_type.name,
                    limit
                ))
