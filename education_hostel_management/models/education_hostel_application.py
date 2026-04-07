from odoo import api, fields, models, _
from odoo.exceptions import UserError




class EducationHostelApplication(models.Model):
    _name = 'education.hostel.application'
    _description = 'Education Hostel Application'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(
        string='Name', default='New', help='Sequence Number for Application.',readonly=True)
    admission_no = fields.Many2one(
        'education.application',
        string='Admission No',
        domain=[('state', 'in', ('admission', 'enrolled'))],
        context={'use_admission_no': True}
    )

    student_id = fields.Many2one(
        'res.partner',
        string='Student',
        domain="[('program_id', '=', program_id), ('class_id', '=', class_id),('position_role','=', 'student'),('hostel','=',True)]"
    )
    # address fields
    street = fields.Char(string='Street', help='Hostel Street')
    street2 = fields.Char(string='Street2', help='Hostel Street2')
    zip = fields.Char(string='Zip Code', change_default=True, help='Zip Code')
    city = fields.Char(string='City', help='City of hostel')
    state_id = fields.Many2one("res.country.state", string='State', ondelete='restrict',
                               domain="[('country_id', '=?', country_id)]")
    country_id = fields.Many2one('res.country', string='Country', ondelete='restrict')
    country_code = fields.Char(related='country_id.code', string="Country Code")
    email = fields.Char(string='Email', help='Email Id of hostel')
    phone = fields.Char(string='Phone', required=True, help='Phone Number')
    mobile = fields.Char(string='Mobile', required=True, help='Mobile Number')
    state = fields.Selection(
        [
            ('draft', 'Draft'),
            ('submitted', 'Submitted'),
            ('allocated', 'Allocated'),
            ('vacated', 'Vacated')
        ],
        string='Status',
        default='draft',
        tracking=True
    )
    program_id = fields.Many2one('education.program',string='Program', required=True)
    class_id = fields.Many2one('education.class',string='Class', required=True)
    parent_name = fields.Char(string='Parent Name')
    guardian_name = fields.Char(string='Guardian Name')
    gender = fields.Selection([ ('male', 'Male'),('female', 'Female'),
        ('other', 'Other'),], string='Gender')
    dob = fields.Date(
        string='Date of Birth',
        help='Student date of birth.'
    )
    id_no = fields.Char('Aadhar No. / ID No.', help='Government-issued ID number', required=True)
    relation = fields.Char(string='Relation', help="Relationship of the guardian to the applicant")
    father_name = fields.Char(string='Father Name')
    mother_name = fields.Char(string='Mother Name')
    contact_no = fields.Char(string='Contact Number')
    emergency_phone = fields.Char(string='Emergency Phone Number')
    blood_group = fields.Selection([
        ('a+', 'A+'), ('a-', 'A-'),
        ('b+', 'B+'), ('b-', 'B-'),
        ('ab+', 'AB+'), ('ab-', 'AB-'),
        ('o+', 'O+'), ('o-', 'O-'),
    ], string='Blood Group')
    guardian = fields.Char(
        string='Guardians',
        help='Enter the student’s guardians or parents.'
    )
    notes = fields.Text(string='Notes',help='Additional notes about the student.')
    contact_address = fields.Text('Permanent Address')
    emergency_phone = fields.Char('Emergency Phone Number')
    allocation_detail_ids = fields.One2many('education.hostel.room.allocation',
                                            'hostel_application_id',
                                            string="Allocation Details",)
    photo = fields.Binary(string='Image',
                          help='Upload a photo of the student.'
                          )


    @api.model_create_multi
    def create(self, vals_list):
        """override create method for reference generation"""
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('education.hostel.application') or _('New')
        return super().create(vals_list)

    def action_submit(self):
        for rec in self:
            rec.state = 'submitted'

    def action_allocate(self):
        for rec in self:
            if not rec.allocation_detail_ids:
                raise UserError(_("Please choose at least one room."))
            active_lines = rec.allocation_detail_ids.filtered(lambda l: not l.vacated_date)
            if not active_lines:
                raise UserError(_("Please allocate a room first."))
            if len(active_lines) > 1:
                raise UserError(_("Please choose Vacated Date."))
            rec.state = 'allocated'

    def action_vacate(self):
        for rec in self:
            if not rec.allocation_detail_ids:
                raise UserError(_("No room allocated."))
            if any(not line.vacated_date for line in rec.allocation_detail_ids):
                raise UserError(_("Please set Vacated Date for all allocation lines."))
            rec.state = 'vacated'

    def action_reset_draft(self):
        for rec in self:
            rec.state = 'draft'
