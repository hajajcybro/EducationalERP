from odoo import models, fields, api

class EducationProgram(models.Model):
    _name = 'education.program'
    _description = 'Education Program'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string="Program Name", required=True)
    code = fields.Char(string="Code", required=True)
    duration = fields.Float(string=" Duration (Years) ", required=True,
                             help="Total program duration in years")
    program_type = fields.Selection([
        ('semester', 'Semester System'),
        ('annual', 'Annual System'),
        ('trimester', 'Trimester System'),
        ('custom', 'Custom'),
    ], string='Program Type', default='semester', required=True)

    session_duration = fields.Float(string='Sessions per Year',
                                      help='Number of sessions/semesters per year')
    total_sessions = fields.Integer(
        string='Total Sessions',
        compute='_compute_total_sessions',
        store=True,
        help='Total number of sessions for the entire program duration'
    )
    credit_hours = fields.Float(string="Total Credit Hours")
    description = fields.Text(string="Description")
    active = fields.Boolean(default=True, string="Active")

    session_ids = fields.One2many('education.session', 'program_id', string='Sessions')
    course_ids = fields.One2many('education.course', 'program_id', string='All Courses')


    _sql_constraints = [
        ('unique_program_code', 'unique(code)', 'Program code must be unique!'),
    ]

    @api.onchange('program_type')
    def _onchange_program_type(self):
        """Set default sessions per year automatically based on program type."""
        if self.program_type == 'semester':
            self.session_duration = 2
        elif self.program_type == 'trimester':
            self.session_duration = 3
        elif self.program_type == 'annual':
            self.session_duration = 1
        elif self.program_type == 'custom':
            self.session_duration = 0

    @api.depends('duration', 'session_duration', 'program_type')
    def _compute_total_sessions(self):
        """Compute total sessions based on duration × sessions per year.

        """
        for rec in self:
            if not rec.duration:
                rec.total_sessions = 0
                continue
            if rec.program_type == 'custom':
                rec.total_sessions = 1
            elif rec.duration and rec.session_duration:
                rec.total_sessions = int(rec.duration * rec.session_duration)
            else:
                rec.total_sessions = 0



