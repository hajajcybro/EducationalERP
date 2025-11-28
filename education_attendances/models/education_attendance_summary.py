# -*- coding: utf-8 -*-
from odoo import models, fields, api
from collections import defaultdict

class EducationAttendanceSummary(models.Model):
    _name = 'education.attendance.summary'
    _description = 'Attendance Summary'
    _rec_name = 'student_id'

    student_id = fields.Many2one(
        'res.partner',domain=[('position_role','=','student')],
        string="Student",
        required=True,
    )
    summary_type = fields.Selection([
        ('daily', 'Daily'),
        ('monthly', 'Monthly'),
        ('annual', 'Annual'),
        ('subject', 'Subject-wise'),
    ], required=True)

    date = fields.Date()
    month = fields.Char()
    year = fields.Char()

    subject_id = fields.Many2one('education.course')

    # Calculated values
    total_present = fields.Integer()
    total_absent = fields.Integer()
    total_leave = fields.Integer()

    attendance_percentage = fields.Float(
        compute="_compute_percentage",
        store=True
    )
    class_id = fields.Many2one(
        'education.class',
        related='student_id.class_id',
        store=True,
        readonly=True
    )
    _sql_constraints = [
        ('unique_summary',
         'unique(student_id, summary_type, date, month, year, subject_id)',
         'Summary record already exists!')
    ]

    # @api.depends('total_present', 'total_absent', 'total_leave')
    # def _compute_percentage(self):
    #     for rec in self:
    #         total = rec.total_present + rec.total_absent + rec.total_leave
    #         rec.attendance_percentage = (rec.total_present / total * 100) if total else 0.0

    @api.depends('total_present', 'total_absent', 'total_leave')
    def _compute_percentage(self):
        # read policy (string → boolean)
        conf = self.env['ir.config_parameter'].sudo().get_param(
            'education_attendances.count_excused_as_present'
        )
        enable = True if conf == 'True' else False
        for rec in self:
            present = rec.total_present
            leave = rec.total_leave
            absent = rec.total_absent
            # numerator
            if enable:
                print('enable')
                numerator = present + leave
            else:
                print('not')
                numerator = present
            # denominator always includes leave
            denominator = present + leave + absent

            rec.attendance_percentage = (numerator / denominator * 100) if denominator else 0.0

    def action_recalculate_all(self):
        """
           Recalculate ALL attendance summary records
           based on the CURRENT summary mode saved in settings.
           """
        print('action recalculation')
        mode = self.env['ir.config_parameter'].sudo().get_param(
            'education_attendances.summary_mode'
        )
        # remove old summary records
        self.search([]).unlink()
        lines = self.env['education.attendance.line'].search([
            ('attendance_id.state', '=', 'validated')
        ])
        if not lines:
            print("No validated attendance found — nothing to recalculate.")
            return

        if mode == 'daily':
            self._build_daily(lines)
        elif mode == 'monthly':
            self._build_monthly(lines)
        elif mode == 'annual':
            self._build_annual(lines)
        elif mode == 'subject':
            self._build_subject(lines)

    def _build_daily(self, lines):
         """One record per student per date."""
         print('daily')
         groups = defaultdict(list)
         for line in lines:
             date = line.attendance_id.date
             if not date:
                 continue
             key = (line.student_id.id, date)
             groups[key].append(line)

         for (student_id, date), group_lines in groups.items():
             self._create_summary_from_lines(
                 student_id=student_id,
                 summary_type='daily',
                 date=date,
                 lines=group_lines,
             )

    def _build_subject(self, lines):
        """One record per student per subject."""
        print('build subject')
        groups = defaultdict(list)
        for line in lines:
            attendance = line.attendance_id
            subject = attendance.timetable_line_id.subject_id
            print(subject)
            if not subject:
                continue
            key = (line.student_id.id, subject.id)
            groups[key].append(line)

        for (student_id, subject_id), group_lines in groups.items():
            self._create_summary_from_lines(
                student_id=student_id,
                summary_type='subject',
                subject_id=subject_id,
                lines=group_lines,
            )

    def _build_annual(self, lines):
        """One record per student per year."""
        groups = defaultdict(list)
        for line in lines:
            date = line.attendance_id.date
            if not date:
                continue
            year = str(date.year)
            key = (line.student_id.id, year)
            groups[key].append(line)
        for (student_id, year), group_lines in groups.items():
            self._create_summary_from_lines(
                student_id=student_id,
                summary_type='annual',
                year=year,
                lines=group_lines,
            )

    def _build_monthly(self, lines):
        """ One record per student per (year, month).
        Month = calendar month, taken from attendance.date.month."""
        groups = defaultdict(list)
        for line in lines:
            date = line.attendance_id.date
            if not date:
                continue
            year = str(date.year)
            month = str(date.month)  # e.g. "11"
            key = (line.student_id.id, year, month)
            groups[key].append(line)

        for (student_id, year, month), group_lines in groups.items():
            self._create_summary_from_lines(
                student_id=student_id,
                summary_type='monthly',
                year=year,
                month=month,
                lines=group_lines,
            )

    def _create_summary_from_lines(self,student_id, summary_type, date=False, month=False,year=False, subject_id=False, lines=None,):
        """Create one summary record from a list of attendance lines."""
        lines = lines or []
        total_present = sum(1 for l in lines if l.status == 'present')
        total_absent = sum(1 for l in lines if l.status == 'absent')
        total_leave = sum(1 for l in lines if l.status == 'leave')

        self.create({
            'student_id': student_id,
            'summary_type': summary_type,
            'date': date,
            'month': month,
            'year': year,
            'subject_id': subject_id or False,
            'total_present': total_present,
            'total_absent': total_absent,
            'total_leave': total_leave,
        })

