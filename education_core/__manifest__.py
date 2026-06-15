{
    "name": "Education ERP — Core",
    "version": "19.0.4.0.0",
    "category": "Education",
    "summary": "Student management, enrollment, attendance, timetable, programs, classes",
    "description": """
Education ERP — Core
====================

Sprint 1: Departments, Academic Years, Programs, Classes, Timetable.
Sprint 2: Student Applications, Enrollment, Documents, Portal Accounts, Email Templates.
Sprint 3: Timetable Slots, Attendance (per-period), Leave Requests, 75% Threshold Cron,
          PDF Attendance Report, Faculty Module.
Sprint 4: Classroom / Exam Hall management (edu.classroom).

Part of the Educational ERP — LMS System built on Odoo 19 Community Edition
by Cybrosys Techno Solutions for Hajaj (Product Owner).

Version: 19.0.4.0.0  |  License: LGPL-3
    """,
    "author": "Cybrosys Techno Solutions",
    "website": "https://www.cybrosys.com",
    "license": "LGPL-3",
    "depends": ['education_config', 'mail', 'portal'],
    "data": [
        # ── Security (always first) ────────────────────────────────────
        "security/ir.model.access.csv",
        "security/record_rules.xml",
        # ── Sequences & seed data ──────────────────────────────────────
        "data/ir_sequence.xml",
        "data/document_type_data.xml",
        # ── Email templates & cron ─────────────────────────────────────
        "data/mail_templates.xml",
        "data/ir_cron.xml",
        # ── Views — Sprint 1 ──────────────────────────────────────────
        "views/department_views.xml",
        "views/academic_year_views.xml",
        "views/program_views.xml",
        "views/class_views.xml",
        "views/timetable_views.xml",
        # ── Views — Sprint 2 ──────────────────────────────────────────
        "views/document_type_views.xml",
        "views/application_views.xml",
        "views/enrollment_views.xml",
        "views/portal_templates.xml",
        # ── Views — Sprint 3 ──────────────────────────────────────────
        "views/attendance_views.xml",
        # ── Views — Sprint 4 ──────────────────────────────────────────
        "views/classroom_views.xml",
        # ── Reports ────────────────────────────────────────────────────
        "report/attendance_report.xml",
        # ── Menus (always last) ────────────────────────────────────────
        "views/menus.xml",
    ],
    "demo": [],
    "installable": True,
    "application": True,
    "auto_install": False,
    "sequence": 3,
}
