from email.policy import default

from odoo import fields, models


class DocumentDocument(models.Model):
    """For managing document type"""
    _name = 'education.document.type'
    _description = "Documents Type"

    name = fields.Char(string='Name', required=True,
                       help="Name of the document type (e.g : Certificate)")
    description = fields.Char(string='Description', help="Note about the type")
    limit = fields.Integer(
        string='Upload Limit', default=1,
        help='Maximum number of documents that can be uploaded for this type.'
    )