# -*- coding: utf-8 -*-
from odoo import api, fields, models,_
from odoo.exceptions import ValidationError


class EducationDocument(models.Model):
    """ This model represents education.document."""
    _name = 'education.document'
    _description = 'Education Document'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    student_id = fields.Many2one(
        'res.partner',
        string='Student',
        required=True,
        ondelete='cascade',
        domain=[('is_student', '=', True)]
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
    name = fields.Char(string = 'Name', compute="_compute_name",
    store=True)
    photo = fields.Binary(string="Photo")

    @api.depends('student_id', 'admission_no', 'document_type')
    def _compute_name(self):
        for rec in self:
            student = rec.student_id.name or ''
            admission = rec.admission_no or ''
            doc_type = rec.document_type.name or ''
            rec.name = f"{student} - {admission} - {doc_type}"

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

    @api.onchange('student_id')
    def _onchange_student_id_set_photo(self):
        """When selecting a student, auto-fill photo if student has one."""
        if self.student_id and self.student_id.image_1920:
            self.photo = self.student_id.image_1920
        else:
            self.photo = False

    @api.model_create_multi
    def create(self, vals_list):
        """ Set the student's profile image from the uploaded photo."""
        records = super().create(vals_list)
        for rec in records:
            if rec.photo:
                rec.student_id.image_1920 = rec.photo
        return records

    def write(self, vals):
        """When a photo is added here, update the student's profile photo too."""
        res = super().write(vals)
        if 'photo' in vals and vals['photo']:
            self.student_id.image_1920 = vals['photo']
        return res
