# -*- coding: utf-8 -*-
{
    'name': 'Education Mobile & Portal Access',
    'version': '19.0.1.0.0',
    'category': 'Education',
    'sequence':-329,
    'description': '''Manage portal and mobile access''',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['base', 'mail','website','education_core' ,'portal',],
    'data': [
        'views/education_application_template.xml',
        'views/education_menu.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}