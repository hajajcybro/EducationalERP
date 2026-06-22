# -*- coding: utf-8 -*-
{
    "name": "Education ERP — LMS",
    "version": "19.0.1.0.0",
    "category": "Education",
    "summary": "Courses, lessons, quiz engine, completion tracking and certificates",
    "description": """
Education ERP — LMS
===================

Courses, lessons, quiz engine, completion tracking and certificates.

Part of the Educational ERP — LMS System built on Odoo 19 Community Edition
by Cybrosys Techno Solutions for Hajaj (Product Owner).

Version: 19.0.1.0.0  |  License: LGPL-3
    """,
    "author": "Cybrosys Techno Solutions",
    "website": "https://www.cybrosys.com",
    "license": "LGPL-3",
    "depends": ["education_core", "education_security",  "mail"],
    "data": [
        "security/ir.model.access.csv",
        "security/record_rules.xml",
        "views/lms_views.xml",
        "report/certificate_report.xml",
        "views/menus.xml",
    ],
    "demo": [],
    "installable": True,
    "application": False,
    "auto_install": False,
    "sequence": 13,
}
