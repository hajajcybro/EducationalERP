# -*- coding: utf-8 -*-
{
    'name': 'Education Library Management',
    'version': '19.0.1.0.0',
    'category': 'Education',
    'sequence':-333,
    'summary': 'Basic library management - books, members, and transactions',
    'description': '''
        Education Library Management - Basic
        ====================================
        * Book cataloging
        * Member management
        * Issue and return books
        * Fine calculation
    ''',
    'author': 'Your Company',
    'website': 'https://www.yourcompany.com',
    'depends': ['base', 'mail','sale','account',
                'website','portal'],
    'data': [
        'security/library_security.xml',
        'security/ir.model.access.csv',
        'data/library_sequence.xml',
        'data/library_product_data.xml',
        'data/library_email_templates.xml',
        'data/library_cron.xml',
        'views/education_library_category_views.xml',
        'views/education_library_book_views.xml',
        'views/education_library_member_views.xml',
        'views/education_library_transaction_views.xml',
        'views/education_library_reservation_views.xml',
        'views/res_config_settings_views.xml',
        'wizards/library_usage_wizard_views.xml',
        'wizards/library_stock_wizard_views.xml',
        'report/library_usage_report_template.xml',
		'report/ir_actions_report.xml',
        'report/library_stock_report_template.xml',
        'wizards/library_overdue_wizard_views.xml',
        'report/library_overdue_books_template.xml',
        'views/portal.xml',
        'views/portal_education_library.xml',
        'views/portal_education_library_book.xml',
        'views/portal_education_library_history.xml',
        'views/education_library_menus.xml',
],
    'assets': {
        'web.assets_backend': [
            # 'education_library/static/src/js/action_manager.js',
        ],
    },
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}