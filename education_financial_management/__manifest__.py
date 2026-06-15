{
    "name": "Education ERP — Financial Management",
    "version": "19.0.5.0.0",
    "category": "Education",
    "summary": "Fee structures, invoices, payments, overdue reminders and fee reports",
    "description": """
Education ERP — Financial Management
====================================

* Fee plan master with components (tuition, lab, transport, etc.)
* Auto-invoice generation from enrollment fee plan
* Scholarship / concession deduction on invoice
* Daily overdue reminder cron + email notification
* Fee Receipt PDF report (QWeb)
* Outstanding Fees pivot & graph dashboard
* Enrolled-invoice shortcut in Fees menu

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
        "account",
        "mail",
    ],
    "data": [
        "security/ir.model.access.csv",
        "data/mail_template_fee_overdue.xml",
        "data/ir_cron.xml",
        "views/fee_plan_views.xml",
        "views/menus.xml",
        "report/fee_receipt_report.xml",
    ],
    "demo": [],
    "installable": True,
    "application": False,
    "auto_install": False,
    "sequence": 50,
}
