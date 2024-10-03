# -*- coding: utf-8 -*-
##############################################################################
#    A part of Educational ERP Project <https://www.educationalerp.com>

#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Subina P (odoo@cybrosys.com)
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
##############################################################################
{
    'name': 'Educational Transport Management',
    'version': '16.0.1.0.0',
    'category': 'Extra Tools',
    'summary': """Complete Transportation management""",
    'description': ' It is a holistic, integrated student Transportation '
                   'Management Software System. The core functionalism includes '
                   'bus routing,trip and vehicles management.',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'website': "http://www.educationalerp.com",
    'depends': ['fleet', 'education_core', 'education_fee'],
    'data': [
        'security/education_transportation_rule.xml',
        'security/ir.model.access.csv',
        'views/education_trip_views.xml',
        'views/education_stop_views.xml',
        'views/fleet_vehicle_views.xml',
        'views/education_student_views.xml',

    ],
    'demo': ['demo/education_transport_data.xml',
             ],
    'images': ['static/description/banner.jpg'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': True,
}
