 # -*- coding: utf-8 -*-
{
    'name': 'Education Audit & Activity Tracking',
    'version': '19.0.1.0.0',
    'summary': 'Manage Educational Audit & Activity Tracking',
    'category': 'Education',
    'sequence': -330,
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['education_core'],
    'data' : [
        'security/ir.model.access.csv',
        'views/education_audit_log.xml',
        'views/menu.xml',
    ],
    'license': 'AGPL-3',
    'installable': True,
    'application': True,
    'auto_install': False,
}