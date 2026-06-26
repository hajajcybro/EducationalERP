{
    "name": "Education ERP — Notifications",
    "version": "19.0.1.0.0",
    "category": "Education",
    "summary": "Email queue, SMS, in-app inbox notifications and cron reminders",
    "description": """
Education ERP — Notifications
=============================

Email queue, SMS, in-app inbox notifications and cron reminders.

Part of the Educational ERP — LMS System built on Odoo 19 Community Edition
by Cybrosys Techno Solutions for Hajaj (Product Owner).

Version: 19.0.1.0.0  |  License: LGPL-3
    """,
    "author": "Cybrosys Techno Solutions",
    "website": "https://www.cybrosys.com",
    "license": "LGPL-3",
    "depends": ["education_core", "education_security", "mail", "sms"],
    "data": [
        "security/ir.model.access.csv",
        "data/ir_cron.xml",
        "views/notification_views.xml",
        "views/menus.xml",
    ],
    "demo": [],
    "installable": True,
    "application": False,
    "auto_install": False,
    "sequence": 16,
}
