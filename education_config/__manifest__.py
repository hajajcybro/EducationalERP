{
    "name": "Education ERP — Configuration",
    "version": "19.0.1.0.0",
    "category": "Education",
    "summary": "Institution profile, branding and system-level configuration",
    "description": """
Education ERP — Configuration
=============================

Institution profile, branding and system-level configuration.

Part of the Educational ERP — LMS System built on Odoo 19 Community Edition
by Cybrosys Techno Solutions for Hajaj (Product Owner).

Version: 19.0.1.0.0  |  License: LGPL-3
    """,
    "author": "Cybrosys Techno Solutions",
    "website": "https://www.cybrosys.com",
    "license": "LGPL-3",
    "depends": ['education_security', 'mail'],
    "data": [
        "security/ir.model.access.csv",
        "data/data.xml",
        "views/institution_profile_views.xml",
        "views/menus.xml",
    ],
    "demo": [],
    "installable": True,
    "application": False,
    "auto_install": False,
    "sequence": 2,
}
