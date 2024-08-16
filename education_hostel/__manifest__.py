# -*- coding: utf-8 -*-
################################################################################
#    A part of Educational ERP Project <https://www.educationalerp.com>
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Arjun S(<https://www.cybrosys.com>)
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
################################################################################
{
    'name': 'Educational Hostel Management',
    'version': '16.0.1.0.0',
    'category': 'Industries',
    'summary': """Complete educational hostel management""",
    'description': 'To efficiently manage the entire residential facility in '
                   'the school, you need to implement effective systems and '
                   'procedures. This involves coordinating various aspects '
                   'such as room assignments, maintenance, security, and '
                   'student welfare.',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "http://www.educationalerp.com",
    'depends': ['education_core', 'education_fee'],
    'data': [
        'security/education_hostel_security.xml',
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'views/education_hostel_views.xml',
        'views/education_room_views.xml',
        'views/education_floor_views.xml',
        'views/education_host_std_views.xml',
        'views/education_mess_views.xml',
        'views/education_application_views.xml',
        'views/education_hostel_leave_views.xml',
        'views/education_student_views.xml',
        'views/education_hostel_menu_items.xml',
    ],
    'demo': ['demo/education_hostel_demo.xml',
             ],
    'images': ['static/description/banner.jpg'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': True,
}
