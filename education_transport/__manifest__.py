{
    "name": "Education ERP — Transport",
    "version": "19.0.1.0.0",
    "category": "Education",
    "summary": "Vehicle fleet, route planning, stop management and student assignments",
    "description": """
Education ERP — Transport
=========================

Vehicle fleet, route planning, stop management and student assignments.

Part of the Educational ERP — LMS System built on Odoo 19 Community Edition
by Cybrosys Techno Solutions for Hajaj (Product Owner).

Version: 19.0.1.0.0  |  License: LGPL-3
    """,
    "author": "Cybrosys Techno Solutions",
    "website": "https://www.cybrosys.com",
    "license": "LGPL-3",
    "depends": ["education_core", "education_security"],
    "data": [
        "security/ir.model.access.csv",
        "views/transport_views.xml",
        "views/menus.xml",
    ],
    "demo": [],
    "installable": True,
    "application": False,
    "auto_install": False,
    "sequence": 20,
}
