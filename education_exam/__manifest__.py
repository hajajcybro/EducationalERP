{
    "name": "Education ERP — Examinations",
    "version": "19.0.4.0.0",
    "category": "Education",
    "summary": "Exam scheduling, hall seating, results, mark sheets and re-evaluation",
    "description": """
Education ERP — Examinations
============================

Sprint 4 (S4-T01 – S4-T11):
  - edu.exam: Exam scheduling, state machine (draft→scheduled→ongoing→published→closed)
  - edu.exam.subject: Subject schedule lines with date, time, hall, marks
  - edu.exam.seating: Auto-assign hall + seat from enrolled students (S4-T02)
  - edu.exam.invigilator: Faculty assigned to halls per exam date (S4-T03)
  - edu.exam.result: Mark entry with percentage, grade (A+–F), pass/fail, rank (S4-T04,T05)
  - edu.exam.result.history: Full audit log of every marks change (S4-T06)
  - Re-evaluation wizard: Request re-check, resets result to draft (S4-T06)
  - Admit Card QWeb PDF: Student name, roll no, schedule, hall, seat, rules (S4-T08)
  - Bulk Mark Entry wizard: Enter all students' marks for one subject at once (S4-T09)
  - Mark Sheet / Progress Card QWeb PDF: All subjects, marks, grades, rank (S4-T10)
  - Unit tests covering all the above (S4-T11)

edu.classroom added to education_core (S4-T12).

Part of the Educational ERP — LMS System built on Odoo 19 Community Edition
by Cybrosys Techno Solutions for Hajaj (Product Owner).

Version: 19.0.4.0.0  |  License: LGPL-3
    """,
    "author": "Cybrosys Techno Solutions",
    "website": "https://www.cybrosys.com",
    "license": "LGPL-3",
    "depends": ['education_core'],
    "data": [
        # ── Security ──────────────────────────────────────────────────
        "security/ir.model.access.csv",
        "security/record_rules.xml",
        # ── Sequences ─────────────────────────────────────────────────
        "data/ir_sequence.xml",
        # ── Views ─────────────────────────────────────────────────────
        "views/exam_views.xml",
        # ── Reports ───────────────────────────────────────────────────
        "report/admit_card_report.xml",
        "report/mark_sheet_report.xml",
        # ── Menus (always last) ────────────────────────────────────────
        "views/menus.xml",
    ],
    "demo": [],
    "installable": True,
    "application": False,
    "auto_install": False,
    "sequence": 11,
}
