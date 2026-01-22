 # -*- coding: utf-8 -*-
{
    'name': 'Education Scholarship',
    'version': '19.0.1.0.0',
    'summary': 'Eduction Scholarship',
    'category': 'Education',
    'sequence': -328,
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['education_core','education_exam'],
    'data': [
        'security/ir.model.access.csv',
        'data/education_scholarship_product.xml',
        'views/education_scholarship_application.xml',
        'views/education_scholarship_view.xml',
        'views/education_scholarship_criteria_view.xml',
        'views/education_scholarship_eligibility_criteria_view.xml',
        'wizard/education_scholarship_wizard.xml',
        'report/ir_actions_report.xml',
        'report/scholarship_report_template.xml',
        'views/education_menu.xml',
    ],
    'assets' : {
                'web.assets_backend': [
                    'education_scholarship/static/src/js/action_manager.js',
                                       ],
        },
    'license': 'AGPL-3',
    'installable': True,
    'application': True,
    'auto_install': False,
}