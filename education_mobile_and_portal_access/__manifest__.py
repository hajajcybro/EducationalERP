# -*- coding: utf-8 -*-
{
    'name': 'Education Mobile & Portal Access',
    'version': '19.0.1.0.0',
    'category': 'Education',
    'sequence':-333,
    'description': '''Manage portal and mobile access''',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['base', 'mail','website','education_core' ],
    'data': [
            'security/student_portal.xml',
            'views/education_portal_menu.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}