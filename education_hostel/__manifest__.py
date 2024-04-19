# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Jumana Haseen (odoo@cybrosys.com)
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
################################################################################
{
    'name': 'Educational Hostel Management',
    'version': '17.0.1.0.0',
    'category': 'Industries',
    'summary': """Complete Hostel management and Efficiently manage the 
     entire residential facility in the school""",
    'description': 'Hostel Management for Educational ERP',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'website': "http://www.educationalerp.com",
    'depends': ['base', 'education_core', 'education_fee'],
    'data': [
        'data/education_hostel_member_data.xml',
        'data/hostel_leave_data.xml',
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/education_hostel_menuitem.xml',
        'views/education_floor_views.xml',
        'views/education_hostel_leave_views.xml',
        'views/education_hostel_views.xml',
        'views/education_host_std_views.xml',
        'views/mess_food_views.xml',
        'views/food_item_views.xml',
        'views/education_mess_views.xml',
        'views/education_room_member_views.xml',
        'views/education_room_views.xml',
        'views/education_application_views.xml',
        'views/education_student_views.xml',

    ],
    'demo': ['demo/hostel_demo_data.xml',
             ],
    'images': ['static/description/banner.png'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': True,
}
