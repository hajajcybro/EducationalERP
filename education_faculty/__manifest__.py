{
    "name": "Education ERP — Faculty",
    "version": "19.0.1.0.0",
    "category": "Education",
    "summary": "Faculty profiles, department assignment, qualifications, workload and overload detection",
    "description": """
Education ERP — Faculty
=======================

Sprint 3 (S3-T11 – S3-T15):
  - Faculty profile model with auto-sequence ID
  - Qualification history per faculty member
  - Workload tracker (weekly teaching periods) with overload alert
  - Optional link to hr.employee for payroll / leave integration
  - Faculty Profile QWeb PDF report

Part of the Educational ERP — LMS System built on Odoo 19 Community Edition
by Cybrosys Techno Solutions for Hajaj (Product Owner).

Version: 19.0.1.0.0  |  License: LGPL-3
    """,
    "author": "Cybrosys Techno Solutions",
    "website": "https://www.cybrosys.com",
    "license": "LGPL-3",
    "depends": ["education_core", "hr"],
    "data": [
        # ── Security ──────────────────────────────────────────────
        "security/ir.model.access.csv",
        "security/record_rules.xml",
        # ── Sequences ─────────────────────────────────────────────
        "data/ir_sequence.xml",
        # ── Views ─────────────────────────────────────────────────
        "views/faculty_views.xml",
        # ── Reports ───────────────────────────────────────────────
        "report/faculty_report.xml",
        # ── Menus ─────────────────────────────────────────────────
        "views/menus.xml",
    ],
    "demo": [],
    "installable": True,
    "application": False,
    "auto_install": False,
    "sequence": 12,
}
