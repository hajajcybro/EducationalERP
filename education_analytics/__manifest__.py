{
    "name": "Education ERP — Analytics",
    "version": "19.0.1.0.0",
    "category": "Education",
    "summary": "SQL-view enrollment analytics and role-based OWL dashboards",
    "description": """
Education ERP — Analytics
=========================

SQL-view enrollment analytics and role-based OWL dashboards.

Part of the Educational ERP — LMS System built on Odoo 19 Community Edition
by Cybrosys Techno Solutions for Hajaj (Product Owner).

Version: 19.0.1.0.0  |  License: LGPL-3
    """,
    "author": "Cybrosys Techno Solutions",
    "website": "https://www.cybrosys.com",
    "license": "LGPL-3",
    "depends": [
        "education_core",
        "education_security",
        "education_exam",
        "education_financial_management",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/analytics_views.xml",
        "views/menus.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "education_analytics/static/src/js/dashboards.js",
        ],
    },
    "demo": [],
    "installable": True,
    "application": False,
    "auto_install": False,
    "sequence": 15,
}
