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
    'depends': ['education_core','mail'],
    'data': [
        'views/education_enrollemt_view.xml',
        'views/menu.xml',
    ],
    'license': 'AGPL-3',
    'installable': True,
    'application': True,
    'auto_install': False,
}