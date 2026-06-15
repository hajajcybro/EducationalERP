{
    "name": "Education ERP — Library",
    "version": "19.0.1.0.0",
    "category": "Education",
    "summary": "Book catalogue, member management, issue/return and fine calculation",
    "description": """
Education ERP — Library
=======================

Book catalogue, member management, issue/return and fine calculation.

Part of the Educational ERP — LMS System built on Odoo 19 Community Edition
by Cybrosys Techno Solutions for Hajaj (Product Owner).

Version: 19.0.1.0.0  |  License: LGPL-3
    """,
    "author": "Cybrosys Techno Solutions",
    "website": "https://www.cybrosys.com",
    "license": "LGPL-3",
    "depends": ["education_core", "education_security", "mail"],
    "data": [
        "security/ir.model.access.csv",
        "data/ir_sequence.xml",
        "data/mail_template_loan_due.xml",
        "data/ir_cron.xml",
        "views/library_views.xml",
        "views/menus.xml",
    ],
    "demo": [],
    "installable": True,
    "application": False,
    "auto_install": False,
    "sequence": 19,
}
