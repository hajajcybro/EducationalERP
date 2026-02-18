from odoo import api, fields, models,_
from odoo.exceptions import UserError, ValidationError


class EducationExamValuation(models.Model):

    _name = 'education.exam.revaluation.creation'
    _description = 'Education Exam ReValuation'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    name = fields.Char(
        string='Name', default='New', help='Sequence Number for revaluation.')
    exam_id = fields.Many2one('education.exam',string='Exam',required=True)
    start_date = fields.Date(string='Start Date',required=True)
    end_date = fields.Date(string='End Date',required=True)
    state = fields.Selection(
        [('draft', 'Draft'), ('ongoing', 'Ongoing'),
         ('closed', 'Closed')], default='draft', help='State of the exam valuation.')


    def action_confirm(self):
        self.state = 'ongoing'

    def action_close(self):
        self.state = 'closed'


    @api.model_create_multi
    def create(self, vals_list):
        """override create method for reference generation"""
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('education.exam.revaluation.creation') or _('New')
        return super().create(vals_list)

    @api.constrains('start_date', 'end_date')
    def _check_dates(self):
        """
           Used to raise a ValidationError if the start date is greater than the end date.
        """
        print("oooooooooooooooooo")
        for rec in self:
            if rec.start_date > rec.end_date:
                raise ValidationError(
                    _("Start date must be less than end date"))

    def action_apply(self):
        self.ensure_one()

        return {
            'type': 'ir.actions.act_window',
            'name': 'Education Exam Revaluation',
            'res_model': 'education.exam.revaluation',
            'view_mode': 'form',
            'target': 'current',
            'context': {
                'default_exam_id': self.exam_id.id,
            }
        }

