{
    "name": "Education ERP — Document Management",
    "version": "19.0.5.0.0",
    "category": "Education",
    "summary": "Document expiry tracking, alert cron and expiry dashboard",
    "description": """
Education ERP — Document Management
=====================================

* Per-document-type configurable expiry alert threshold (days)
* Computed expiry_state on every document: valid / expiring_soon / expired / no_expiry
* Weekly cron sends email alerts for expiring/expired verified documents
* Document Expiry Dashboard (list view filtered to docs with expiry dates)

Part of the Educational ERP — LMS System built on Odoo 19 Community Edition
by Cybrosys Techno Solutions for Hajaj (Product Owner).

Version: 19.0.5.0.0  |  License: LGPL-3
    """,
    "author": "Cybrosys Techno Solutions",
    "website": "https://www.cybrosys.com",
    "license": "LGPL-3",
    "depends": [
        "education_core",
        "education_security",
        "mail",
    ],
    "data": [
        "security/ir.model.access.csv",
        "data/mail_template_doc_expiry.xml",
        "data/ir_cron.xml",
        "views/document_expiry_views.xml",
        "views/menus.xml",
    ],
    "demo": [],
    "installable": True,
    "application": False,
    "auto_install": False,
    "sequence": 60,
}
