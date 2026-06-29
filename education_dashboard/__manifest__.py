{
    "name": "Education ERP — Dashboard",
    "version": "19.0.1.0.0",
    "category": "Education",
    "summary": "Six role-specific OWL dashboards with live KPIs and quick actions",
    "description": """
Education ERP — Dashboard
=========================

Six role-specific OWL dashboards with live KPIs and quick actions.

Part of the Educational ERP — LMS System built on Odoo 19 Community Edition
by Cybrosys Techno Solutions for Hajaj (Product Owner).

Version: 19.0.1.0.0  |  License: LGPL-3
    """,
    "author": "Cybrosys Techno Solutions",
    "website": "https://www.cybrosys.com",
    "license": "LGPL-3",
    "depends": [
        'education_core',
        'education_config',
        'education_security',
        'education_exam',
        'education_analytics',
    ],
    "data": [
        'views/dashboard_actions.xml',
        'views/dashboard_menus.xml',
    ],
    "assets": {
        "web.assets_backend": [
            "education_dashboard/static/src/scss/dashboard.scss",
            "education_dashboard/static/src/js/admin_dashboard.js",
            "education_dashboard/static/src/js/faculty_dashboard.js",
            "education_dashboard/static/src/xml/admin_dashboard.xml",
            "education_dashboard/static/src/xml/faculty_dashboard.xml",
        ],
    },
    "demo": [],
    "installable": True,
    "application": False,
    "auto_install": False,
    "sequence": 25,
}
