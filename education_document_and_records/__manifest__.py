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
        'security/ir.model.access.csv',
        'data/ir_cron.xml',
        'views/education_document_view.xml',
        'views/education_document_type.xml',
        'wizard/education_document_reject_wizard.xml',
        'wizard/education_document_report_wizard.xml',
        'report/ir_actions_report.xml',
        'report/education_document_report_template.xml',
        'views/menu.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'education_document_and_records/static/src/js/action_manager.js',
        ],
    },
    'license': 'AGPL-3',
    'installable': True,
    'application': True,
    'auto_install': False,
}