# -*- coding: utf-8 -*-
from odoo import models, fields, api


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    library_fine_per_day = fields.Float(
        string='Fine Per Day',
        config_parameter='education_library.fine_per_day',
        help='Default fine amount charged per day for overdue books'
    )

    library_student_borrow_days = fields.Integer(
        string='Student Borrow Period (Days)',
        config_parameter='education_library.student_borrow_days',
        help='Default number of days students can borrow books'
    )

    library_faculty_borrow_days = fields.Integer(
        string='Faculty/Staff Borrow Period (Days)',
        config_parameter='education_library.faculty_borrow_days',
        help='Default number of days faculty/staff can borrow books'
    )

    library_max_renewals = fields.Integer(
        string='Maximum Renewals',
        config_parameter='education_library.max_renewals',
        help='Maximum number of times a book can be renewed'
    )

    library_reservation_expiry_hours = fields.Integer(
        string='Reservation Expiry (Hours)',
        config_parameter='education_library.reservation_expiry_hours',
        help='Hours to collect book after it becomes available'
    )

    library_max_reservations_per_member = fields.Integer(
        string='Max Reservations Per Member',
        config_parameter='education_library.max_reservations_per_member',
        help='Maximum active reservations allowed per member'
    )

    library_student_membership_years = fields.Integer(
        string='Student Membership (Years)',
        config_parameter='education_library.student_membership_years',
        help='Default membership duration for students'
    )

    library_faculty_membership_years = fields.Integer(
        string='Faculty/Staff Membership (Years)',
        config_parameter='education_library.faculty_membership_years',
        help='Default membership duration for faculty/staff'
    )

    library_fine_product_id = fields.Many2one(
        comodel_name='product.product',
        string='Fine Product',
        config_parameter='education_library.fine_product_id',
        help='Product used for fine invoices'
    )

    library_send_due_reminders = fields.Boolean(
        string='Send Due Date Reminders',
        default=True,
        config_parameter='education_library.send_due_reminders',
        help='Send email reminders one day before due date'
    )

    library_send_overdue_notifications = fields.Boolean(
        string='Send Overdue Notifications',
        default=True,
        config_parameter='education_library.send_overdue_notifications',
        help='Send email notifications for overdue books'
    )

    library_send_reservation_notifications = fields.Boolean(
        string='Send Reservation Notifications',
        default=True,
        config_parameter='education_library.send_reservation_notifications',
        help='Send email notifications for reservations'
    )

    @api.onchange('library_fine_product_id')
    def _onchange_fine_product(self):
        """Set default fine product on first time"""
        if not self.library_fine_product_id:
            fine_product = self.env.ref(xml_id='education_library.product_library_fine', raise_if_not_found=False)
            if fine_product:
                self.library_fine_product_id = fine_product
