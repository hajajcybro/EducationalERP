# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Gayathri V(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import fields, models


class EducationStudentFinalResult(models.Model):
    """
       Model to store final results of education students.
       """
    _name = 'education.student.final.result'
    _description = 'Student Final Result'
    _rec_name = 'student_id'

    student_id = fields.Many2one('education.student', string="Student",
                                 help='Reference to the student linked to this '
                                      'final result.')
    final_result = fields.Selection([
        ('na', 'Not Applicable'),
        ('pass', 'Pass'),
        ('fail', 'Fail'), ],
        string="Final Result", default='na',
        help="The overall outcome of the student's academic performance.")
    division_id = fields.Many2one('education.class.division', string="Class",
                                  help='Indicates the class division to which'
                                       ' the student belongs.')
    academic_year_id = fields.Many2one('education.academic.year',
                                       string='Academic Year',
                                       help='Represents the academic year '
                                            'during which the final result '
                                            'was recorded.')
    closing_id = fields.Many2one('education.promotion',
                                 string='Academic Year',
                                 help='Identifies the academic year closure '
                                      'or promotion details.')
