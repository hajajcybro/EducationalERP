# -*- coding: utf-8 -*-
from odoo import models, fields, api


class AlumniJobPost(models.Model):
    _name = 'alumni.job.post'
    _description = 'Alumni Job Posting'

    job_title = fields.Char(string='Job Title', required=True)
    company_name = fields.Char(string='Company Name', required=True)
    description = fields.Text(string='Job Description & How to Apply', required=True)
    posted_by_id = fields.Many2one('res.partner', string='Posted By (Alumni)',domain=[('position_role', '=', 'alumni')])
    state = fields.Selection([
        ('draft', 'Draft / Pending Approval'),
        ('published', 'Published'),
        ('closed', 'Closed')
    ], string='Status', default='draft')
    active = fields.Boolean(default=True)