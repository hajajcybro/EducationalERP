# -*- coding: utf-8 -*-
"""
education_dashboard — Dashboard data provider
=============================================
AbstractModel exposing @api.model methods consumed by the Admin and Faculty
OWL dashboard components. Returns plain dicts (KPIs + small chart series) so
the front-end stays dependency-free.
"""
from odoo import api, fields, models


class EduDashboard(models.AbstractModel):
    _name = "edu.dashboard"
    _description = "Education Dashboard Data Provider"

    # ── helpers ───────────────────────────────────────────────────────────

    @api.model
    def _has_field(self, model, fname):
        return model in self.env and fname in self.env[model]._fields

    @api.model
    def _attendance_breakdown(self, domain):
        """Return present/absent/late/excused counts + present-rate % for a
        given attendance domain."""
        Att = self.env["education.attendance"]
        total = Att.search_count(domain)
        out = {"total": total, "rate": 0.0}
        for key in ("present", "absent", "late", "excused"):
            out[key] = Att.search_count(domain + [("state", "=", key)])
        if total:
            out["rate"] = round((out["present"] + out["late"]) * 100.0 / total, 1)
        return out

    # ── ADMIN DASHBOARD ───────────────────────────────────────────────────

    @api.model
    def get_admin_dashboard(self):
        Enrollment = self.env["education.enrollment"]
        Application = self.env["education.application"]
        Exam = self.env["edu.exam"]
        today = fields.Date.today()

        total_students = Enrollment.search_count([("state", "=", "active")])
        total_faculty = self.env["education.faculty"].search_count([])
        total_programs = self.env["education.program"].search_count([])
        total_classes = self.env["education.class"].search_count([])
        pending_applications = Application.search_count([("state", "=", "submitted")])
        upcoming_exams = Exam.search_count([
            ("state", "in", ["scheduled", "ongoing"]),
            ("date_from", ">=", today),
        ])

        # Fees outstanding (field is contributed by financial mgmt module)
        fees_outstanding = 0
        if self._has_field("education.enrollment", "fee_state"):
            fees_outstanding = Enrollment.search_count([
                ("state", "=", "active"),
                ("fee_state", "in", ["overdue", "invoiced", "partial"]),
            ])

        attendance = self._attendance_breakdown([])

        # Students by program (top 8)
        by_program = []
        groups = Enrollment._read_group(
            [("state", "=", "active")],
            groupby=["program_id"],
            aggregates=["__count"],
        )
        for program, count in groups:
            by_program.append({"label": program.name if program else "Unassigned",
                               "value": count})
        by_program.sort(key=lambda r: r["value"], reverse=True)
        by_program = by_program[:8]

        # Applications funnel
        funnel = []
        for state, label in [("draft", "Draft"), ("submitted", "Submitted"),
                             ("approved", "Approved"), ("rejected", "Rejected")]:
            funnel.append({"label": label,
                          "value": Application.search_count([("state", "=", state)])})

        # Recent applications awaiting review
        recent = []
        for app in Application.search([("state", "=", "submitted")],
                                     limit=6, order="id desc"):
            recent.append({
                "id": app.id,
                "name": app.display_name,
                "program": app.program_id.name if app.program_id else "",
            })

        return {
            "kpis": {
                "total_students": total_students,
                "total_faculty": total_faculty,
                "total_programs": total_programs,
                "total_classes": total_classes,
                "pending_applications": pending_applications,
                "upcoming_exams": upcoming_exams,
                "fees_outstanding": fees_outstanding,
                "attendance_rate": attendance["rate"],
            },
            "attendance": attendance,
            "by_program": by_program,
            "funnel": funnel,
            "recent_applications": recent,
        }

    # ── FACULTY DASHBOARD ─────────────────────────────────────────────────

    @api.model
    def _resolve_faculty(self, faculty_id=None):
        Faculty = self.env["education.faculty"]
        if faculty_id:
            return Faculty.browse(faculty_id)
        user = self.env.user
        # 1) via linked HR employee
        fac = Faculty.search([("employee_id.user_id", "=", user.id)], limit=1)
        # 2) via matching work email / login
        if not fac and (user.email or user.login):
            fac = Faculty.search(
                ["|", ("email", "=ilike", user.email or ""),
                 ("email", "=ilike", user.login or "")], limit=1)
        # 3) demo fallback: prefer a faculty who actually teaches a class so
        #    admins previewing the board see populated data
        if not fac:
            teacher = self.env["education.class"].search(
                [("class_teacher_id", "!=", False)], limit=1).class_teacher_id
            fac = teacher or Faculty.search([], limit=1)
        return fac

    @api.model
    def get_faculty_dashboard(self, faculty_id=None):
        faculty = self._resolve_faculty(faculty_id)
        if not faculty:
            return {"faculty": False}

        Class = self.env["education.class"]
        Enrollment = self.env["education.enrollment"]
        Slot = self.env["education.timetable.slot"]
        Exam = self.env["edu.exam"]
        today = fields.Date.today()

        my_classes = Class.search([("class_teacher_id", "=", faculty.id)])
        my_slots = Slot.search([("teacher_id", "=", faculty.id)])
        # Subjects taught (from timetable slots, distinct names)
        subjects = sorted({s.subject for s in my_slots if s.subject})

        my_students = Enrollment.search_count([
            ("class_id", "in", my_classes.ids), ("state", "=", "active"),
        ]) if my_classes else 0

        # Attendance pending: my classes with no attendance marked today
        attendance_pending = 0
        for cls in my_classes:
            if not self.env["education.attendance"].search_count([
                    ("class_id", "=", cls.id), ("date", "=", today)]):
                attendance_pending += 1

        # Upcoming exams touching my classes
        upcoming = Exam.search([
            ("state", "in", ["scheduled", "ongoing"]),
            ("date_from", ">=", today),
            ("class_ids", "in", my_classes.ids),
        ], order="date_from") if my_classes else Exam.browse()

        upcoming_exams = [{
            "id": e.id,
            "name": e.name,
            "date": e.date_from and e.date_from.strftime("%d %b %Y") or "",
            "state": e.state,
        } for e in upcoming[:6]]

        # Per-class roster sizes
        class_rows = [{
            "id": cls.id,
            "name": cls.display_name,
            "students": Enrollment.search_count([
                ("class_id", "=", cls.id), ("state", "=", "active")]),
        } for cls in my_classes]

        attendance = self._attendance_breakdown(
            [("class_id", "in", my_classes.ids)] if my_classes else [("id", "=", 0)])

        return {
            "faculty": {
                "id": faculty.id,
                "name": faculty.name,
                "designation": faculty.designation or "",
                "department": faculty.department_id.name if faculty.department_id else "",
            },
            "kpis": {
                "my_classes": len(my_classes),
                "my_students": my_students,
                "my_subjects": len(subjects),
                "attendance_pending": attendance_pending,
                "upcoming_exams": len(upcoming),
                "weekly_slots": len(my_slots),
            },
            "subjects": subjects[:12],
            "upcoming_exams": upcoming_exams,
            "classes": class_rows,
            "attendance": attendance,
        }
