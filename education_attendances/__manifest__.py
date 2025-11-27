# -*- coding: utf-8 -*-
{
    'name': 'Education Attendance',
    'version': '19.0.1.0.0',
    'summary': 'Manage student and faculty attendance integrated with timetable',
    'category': 'Education',
    'sequence': -333,
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['education_core','mail','base'],
    'data': [
        'security/ir.model.access.csv',
        'views/res_partner_view.xml',
        'views/education_leave_request_view.xml',
        'views/education_attendance_view.xml',
        'views/education_attendance_line_view.xml',
        'views/education_attendance_summary.xml',
        'views/menu.xml',
        'views/res_config_settings_view.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'education_attendances/static/src/css/custom.css',
        ],
    },

    'license': 'AGPL-3',
    'installable': True,
    'application': True,
    'auto_install': False,
}