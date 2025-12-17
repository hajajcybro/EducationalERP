 # -*- coding: utf-8 -*-
{
    'name': 'Education Document & Records',
    'version': '19.0.1.0.0',
    'summary': 'Manage educational document and records',
    'category': 'Education',
    'sequence': -331,
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['education_core'],
    'data' : [
        'views/education_document_view.xml',
        'views/education_document_type.xml',
        'views/menu.xml',
    ],
    'license': 'AGPL-3',
    'installable': True,
    'application': True,
    'auto_install': False,
}