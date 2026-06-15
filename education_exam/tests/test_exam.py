# -*- coding: utf-8 -*-
"""
Unit tests — edu.exam, edu.exam.result, seating (S4-T11)
=========================================================
Covers: exam creation, state machine, seating auto-generation,
mark entry, grade computation, history logging, rank calculation,
and re-evaluation wizard.
"""
from odoo.tests import TransactionCase, tagged
from odoo.exceptions import ValidationError, UserError


@tagged("post_install", "-at_install")
class TestEduExam(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # Academic year
        cls.academic_year = cls.env["education.academic.year"].create({
            "name": "Test Year 2026",
            "date_start": "2026-01-01",
            "date_stop": "2026-12-31",
        })

        # Department & program
        dept = cls.env["education.department"].create({"name": "Test Dept"})
        program = cls.env["education.program"].create({
            "name": "Test Program",
            "department_id": dept.id,
        })

        # Class
        cls.edu_class = cls.env["education.class"].create({
            "name": "Class 10-A",
            "academic_year_id": cls.academic_year.id,
            "program_id": program.id,
        })

        # Classroom
        cls.classroom = cls.env["edu.classroom"].create({
            "room_no": "H101",
            "block": "Exam",
            "capacity": 40,
            "room_type": "hall",
        })

        # Partner for enrollment
        partner1 = cls.env["res.partner"].create({"name": "Alice Test"})
        partner2 = cls.env["res.partner"].create({"name": "Bob Test"})
        partner3 = cls.env["res.partner"].create({"name": "Carol Test"})

        # Application → enrollment helper
        def _make_enrollment(partner):
            app = cls.env["education.application"].create({
                "name": partner.name,
                "partner_id": partner.id,
                "academic_year_id": cls.academic_year.id,
                "program_id": program.id,
            })
            app.action_approve()
            return cls.env["education.enrollment"].create({
                "application_id": app.id,
                "academic_year_id": cls.academic_year.id,
                "class_id": cls.edu_class.id,
                "state": "active",
            })

        cls.enr1 = _make_enrollment(partner1)
        cls.enr2 = _make_enrollment(partner2)
        cls.enr3 = _make_enrollment(partner3)

    # ── Exam CRUD ──────────────────────────────────────────────────────────

    def _make_exam(self):
        return self.env["edu.exam"].create({
            "name": "Mid-Term Nov 2026",
            "exam_type": "mid_term",
            "academic_year_id": self.academic_year.id,
            "date_from": "2026-11-01",
            "date_to": "2026-11-10",
            "class_ids": [(4, self.edu_class.id)],
            "subject_line_ids": [
                (0, 0, {
                    "subject": "Mathematics",
                    "exam_date": "2026-11-01",
                    "max_marks": 100.0,
                    "pass_marks": 40.0,
                }),
                (0, 0, {
                    "subject": "English",
                    "exam_date": "2026-11-03",
                    "max_marks": 100.0,
                    "pass_marks": 40.0,
                }),
            ],
        })

    def test_exam_creation_auto_code(self):
        exam = self._make_exam()
        self.assertNotEqual(exam.code, "New")
        self.assertTrue(exam.code.startswith("EXAM/"))

    def test_exam_date_constraint(self):
        with self.assertRaises(ValidationError):
            self.env["edu.exam"].create({
                "name": "Bad Dates",
                "exam_type": "unit_test",
                "academic_year_id": self.academic_year.id,
                "date_from": "2026-11-10",
                "date_to": "2026-11-01",  # end before start
            })

    # ── State Machine ──────────────────────────────────────────────────────

    def test_state_machine_full_cycle(self):
        exam = self._make_exam()
        self.assertEqual(exam.state, "draft")

        exam.action_schedule()
        self.assertEqual(exam.state, "scheduled")

        exam.action_start()
        self.assertEqual(exam.state, "ongoing")

        # Add a result before publishing
        self.env["edu.exam.result"].create({
            "exam_id": exam.id,
            "enrollment_id": self.enr1.id,
            "subject": "Mathematics",
            "marks_obtained": 75.0,
            "max_marks": 100.0,
            "pass_marks": 40.0,
            "state": "draft",
        })
        exam.action_publish_results()
        self.assertEqual(exam.state, "result_published")

        exam.action_close()
        self.assertEqual(exam.state, "closed")

    def test_schedule_without_subjects_raises(self):
        exam = self.env["edu.exam"].create({
            "name": "No Subjects",
            "exam_type": "unit_test",
            "academic_year_id": self.academic_year.id,
            "date_from": "2026-11-01",
            "date_to": "2026-11-02",
        })
        with self.assertRaises(UserError):
            exam.action_schedule()

    # ── Seating Generation ────────────────────────────────────────────────

    def test_generate_seating(self):
        exam = self._make_exam()
        exam.action_schedule()
        exam.action_generate_seating()

        seating = exam.seating_ids
        self.assertEqual(len(seating), 3)  # 3 enrollments
        roll_nos = seating.mapped("roll_no")
        self.assertEqual(len(set(roll_nos)), 3)  # all unique

    def test_seating_duplicate_prevented(self):
        exam = self._make_exam()
        exam.action_generate_seating()
        with self.assertRaises(Exception):
            self.env["edu.exam.seating"].create({
                "exam_id": exam.id,
                "enrollment_id": self.enr1.id,
                "roll_no": "9999",
            })

    # ── Mark Entry & Grade Computation ───────────────────────────────────

    def _make_result(self, exam, enrollment, subject, marks, max_marks=100.0, pass_marks=40.0):
        return self.env["edu.exam.result"].create({
            "exam_id": exam.id,
            "enrollment_id": enrollment.id,
            "subject": subject,
            "marks_obtained": marks,
            "max_marks": max_marks,
            "pass_marks": pass_marks,
        })

    def test_grade_computation(self):
        exam = self._make_exam()
        r_aplus = self._make_result(exam, self.enr1, "Math", 95)
        r_a = self._make_result(exam, self.enr2, "Math", 82)
        r_fail = self._make_result(exam, self.enr3, "Math", 35)

        self.assertEqual(r_aplus.grade, "A+")
        self.assertEqual(r_aplus.pass_fail, "pass")
        self.assertAlmostEqual(r_aplus.percentage, 95.0)

        self.assertEqual(r_a.grade, "A")
        self.assertEqual(r_a.pass_fail, "pass")

        self.assertEqual(r_fail.grade, "F")
        self.assertEqual(r_fail.pass_fail, "fail")

    def test_absent_result(self):
        exam = self._make_exam()
        r = self._make_result(exam, self.enr1, "English", 0)
        r.write({"absent": True})
        self.assertEqual(r.pass_fail, "absent")
        self.assertEqual(r.grade, "AB")

    def test_marks_exceeds_max_raises(self):
        exam = self._make_exam()
        with self.assertRaises(ValidationError):
            self._make_result(exam, self.enr1, "Science", 105, max_marks=100)

    def test_marks_negative_raises(self):
        exam = self._make_exam()
        with self.assertRaises(ValidationError):
            self._make_result(exam, self.enr1, "History", -5)

    # ── Rank Computation ─────────────────────────────────────────────────

    def test_rank_calculation(self):
        exam = self._make_exam()
        r1 = self._make_result(exam, self.enr1, "Math", 90)
        r2 = self._make_result(exam, self.enr2, "Math", 75)
        r3 = self._make_result(exam, self.enr3, "Math", 60)

        # Force recompute
        (r1 | r2 | r3)._compute_rank()

        self.assertEqual(r1.rank, 1)
        self.assertEqual(r2.rank, 2)
        self.assertEqual(r3.rank, 3)

    # ── History Logging ───────────────────────────────────────────────────

    def test_marks_change_logged_in_history(self):
        exam = self._make_exam()
        result = self._make_result(exam, self.enr1, "Math", 70)
        initial_history = len(result.history_ids)

        result.write({"marks_obtained": 80.0})

        self.assertEqual(len(result.history_ids), initial_history + 1)
        latest = result.history_ids.sorted("change_date", reverse=True)[0]
        self.assertEqual(latest.old_marks, 70.0)
        self.assertEqual(latest.new_marks, 80.0)
        self.assertEqual(latest.delta, 10.0)

    # ── Re-evaluation Wizard ──────────────────────────────────────────────

    def test_reevaluation_resets_to_draft(self):
        exam = self._make_exam()
        result = self._make_result(exam, self.enr1, "Math", 65)
        result.write({"state": "published"})

        wizard = self.env["edu.exam.reevaluation.wizard"].create({
            "result_id": result.id,
            "reason": "Marks tallied incorrectly by teacher",
        })
        wizard.action_submit()

        self.assertEqual(result.state, "draft")
        history = result.history_ids.filtered(
            lambda h: "RE-EVALUATION" in (h.reason or "")
        )
        self.assertTrue(history)
