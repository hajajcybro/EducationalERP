{
    "name": "Education ERP — Integrations",
    "version": "19.0.1.0.0",
    "category": "Education",
    "summary": "REST API endpoints, payment webhook stub and import/export controllers",
    "description": """
Education ERP — Integrations
============================

REST API endpoints, payment webhook stub and import/export controllers.

Part of the Educational ERP — LMS System built on Odoo 19 Community Edition
by Cybrosys Techno Solutions for Hajaj (Product Owner).

Version: 19.0.1.0.0  |  License: LGPL-3
    """,
    "author": "Cybrosys Techno Solutions",
    "website": "https://www.cybrosys.com",
    "license": "LGPL-3",
    "depends": ["education_core", "education_security", "portal", "website"],
    "data": [
        "security/ir.model.access.csv",
        "views/portal_templates.xml",
    ],
    "demo": [],
    "installable": True,
    "application": False,
    "auto_install": False,
    "sequence": 24,
}
