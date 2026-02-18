from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class EducationExam(models.Model):
    """
        Model representing Education Exams.
    """
    _name = 'education.exam'
    _description = 'Education Exam'
    _inherit = ['mail.thread', 'mail.activity.mixin']


    name = fields.Char(
        string='Name', default='New', help='Name of the education exam.')
    program_id = fields.Many2one('education.program', string="Program")
    class_id = fields.Many2one('education.class', string="Class")
    session_id = fields.Many2one('education.session', string="Session",required=True,domain="[('program_id', '=', program_id),('state','=','active')]")
    academic_year_id = fields.Many2one('education.academic.year', string='Academic Year',related='session_id.academic_year_id',required=True)
    exam_type_id = fields.Many2one('education.exam.type', string='Exam Type')

    start_date = fields.Date(string='Start Date',required=True)
    end_date = fields.Date(string='End Date',required=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('closed', 'closed'),
    ], default='draft', string="Status", tracking=True)
    course_line_ids = fields.One2many('education.exam.line', 'exam_id',
        string='Course', help='Course associated with the exam.')
    valuation_completed = fields.Boolean(string='Valuation Completed',defauilt=False,copy=False)


    def action_confirm(self):
        """This function is used to confirm exam"""

        if not self.course_line_ids:
            raise UserError(_('Please Add Courses'))

        self.name = (
            f"{self.program_id.name}-"
            f"{self.session_id.name}-"
            f"{self.exam_type_id.name}-"
            f"{self.start_date}"
        )

        # Find students of the class
        students = self.env['res.partner'].search([
            ('class_id', '=', self.class_id.id), ('position_role', '=', 'student')
        ])

        if not students:
            raise UserError(_('No students found in this class.'))

        template = self.env.ref('education_exam.email_template_exam_published')

        for student in students:
            email = student.email or student.partner_id.email
            if email:
                template.send_mail(
                    self.id,
                    email_values={'email_to': email},
                    force_send=True
                )
        self.name = str(self.program_id.name) + '-' + str(self.session_id.name) + '-' + str(
            self.exam_type_id.name) + '-' + str(self.start_date)
        self.state = 'published'

    def action_cancel(self):
        """This function is used to cancel exam"""
        self.state = 'closed'


    @api.model_create_multi
    def create(self, vals_list):
        """Override create method to generate name based on given details"""
        records = super().create(vals_list)
        for rec in records:
            if rec.start_date and rec.end_date:
                rec.name = str(rec.program_id.name) + '-' + str(rec.session_id.name) + '-' + str(
                    rec.exam_type_id.name) + '-' + str(rec.start_date.strftime('%d-%m-%Y'))+ 'to' + str(rec.end_date.strftime('%d-%m-%Y'))
        return records


    @api.constrains('start_date', 'end_date')
    def _check_dates(self):
        """
           Used to raise a ValidationError if the start date is greater than the end date.
        """
        for rec in self:
            if rec.start_date > rec.end_date:
                raise ValidationError(
                    _("Start date must be less than end date"))

    def action_draft(self):
        self.state = 'draft'


    def cron_send_result_email(self):
        print("IIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIII",self)
        exam_ids = self.search([('state', '=', 'published'),('valuation_completed','=',False)])
        print("kkkkkkkkkkkkkkkkkkkkkkkkkkkk",exam_ids)
        for exam_id in exam_ids:
            print("iiiiiiiiiiiiiii",exam_id,exam_id.valuation_completed,
                  exam_id.class_id)
            result_ids = self.env['education.exam.result'].search(
                [('exam_id', '=', exam_id.id),
                 ('class_id', '=', exam_id.class_id.id),('valuation_completed','=',False),])
            print("ooooooooooooooo",result_ids)
            for result in result_ids:
                print("eeee",result.result_line_ids)
                print("yyyyyyyyyyyyyy",exam_id.course_line_ids)
                if len(result.result_line_ids) == len(exam_id.course_line_ids):
                    print("uuuuuuuuuuuuuuuuu")
                    student_email = result.student_id.email
                    template = self.env.ref(
                        'education_exam.email_template_exam_result_published'
                    )
                    email_values = {
                        'email_to': student_email,
                    }

                    template.with_context(
                        student_name=result.student_id.name,
                        mail_notify_force_send=False,
                        mail_post_autofollow=False,
                        mail_create_nosubscribe=True,
                        mail_auto_subscribe_no_notify=True
                    ).send_mail(
                        exam_id.id,
                        email_values=email_values,
                        force_send=True
                    )
                    exam_id.valuation_completed= True
                    result.valuation_completed= True









