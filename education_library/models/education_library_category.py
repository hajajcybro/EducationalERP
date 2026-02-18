# -*- coding: utf-8 -*-

from odoo import models, fields, api

class EducationLibraryCategory(models.Model):
    _name = 'education.library.category'
    _description = 'Library Book Category'
    _order = 'name'

    name = fields.Char(string='Category Name', required=True)
    description = fields.Text(string='Description')
    book_ids = fields.One2many(comodel_name='education.library.book', inverse_name='category_id', string='Books')
    book_count = fields.Integer(string='Books', compute='_compute_book_count')

    @api.depends('book_ids')
    def _compute_book_count(self):
        for category in self:
            category.book_count = len(category.book_ids)

