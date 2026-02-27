# -*- coding: utf-8 -*-
{
    'name': 'Education Notifications & Communication',
    'version': '19.0.1.0.0',
    'summary': 'Unified notification system for students, parents, teachers',
    'category': 'Education',
    'sequence': -333,
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['base', 'mail','mass_mailing','education_core'],
    'data': [
        'security/ir.model.access.csv',
        'views/education_notification_views.xml',
        'views/mailing_mailing_views.xml',

    ],
    'license': 'AGPL-3',
    'installable': True,
    'application': True,
    'auto_install': False,
}