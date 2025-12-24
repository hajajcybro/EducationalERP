 # -*- coding: utf-8 -*-
{
    'name': 'Education Financial Management',
    'version': '19.0.1.0.0',
    'summary': 'Eduction Financial Management',
    'category': 'Education',
    'sequence': -329,
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['education_core'],
    'data': [
         'views/education_fee_installment_view.xml',
         'views/education_fee_plan_view.xml'
         'views/menu.xml',
    ],
    'license': 'AGPL-3',
    'installable': True,
    'application': True,
    'auto_install': False,
}