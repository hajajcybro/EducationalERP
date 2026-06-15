# -*- coding: utf-8 -*-
"""
education_lms — Unit Tests
===========================
Covers:
  - Course publish state transition
  - Lesson count computed field
  - LMS enrollment creation and completion
  - Duplicate enrollment constraint
  - Quiz attempt pass/fail computation
  - Quiz question count computed field
"""
from datetime import date, timedelta
from odoo.tests.common import TransactionCase, tagged
from odoo.exceptions import ValidationError


@tagged("post_install", "-at_install")
class TestLms(TransactionCase):
    """Unit tests for LMS models."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # ── Academic year ──────────────────────────────────────────────────
        cls.academic_year = cls.env["education.academic.year"].create({
            "name": "LMS Test Year 2025-2026",
            "code": "LMSTST26",
            "date_start": date(2025, 7, 1),
            "date_end": date(2026, 6, 30),
            "is_current": False,
        })

        # ── Department + Program ───────────────────────────────────────────
        cls.department = cls.env["education.department"].create({
            "name": "LMS Test Department",
            "code": "LMSDEPT",
        })
        cls.program = cls.env["education.program"].create({
            "name": "LMS Test Program",
            "code": "LMSPROG",
            "department_id": cls.department.id,
            "degree_type": "bachelor",
            "duration_years": 3,
        })

        # ── Application → approval → enrollment ───────────────────────────
        cls.application = cls.env["education.application"].create({
            "first_name": "LMS",
            "last_name": "Student",
            "date_of_birth": date.today() - timedelta(days=365 * 20),
            "gender": "male",
            "email": "lms.student@example.com",
            "phone": "1111111111",
            "program_id": cls.program.id,
            "academic_year_id": cls.academic_year.id,
        })
        cls.application.action_submit()
        cls.application.action_approve()
        cls.enrollment = cls.application.enrollment_id

        # ── Course category ────────────────────────────────────────────────
        cls.category = cls.env["edu.lms.course.category"].create({
            "name": "LMS Test Category",
        })

        # ── LMS Course ─────────────────────────────────────────────────────
        cls.course = cls.env["education.lms.course"].create({
            "title": "Introduction to Testing",
            "category_id": cls.category.id,
            "state": "draft",
            "enrollment_mode": "open",
        })

        # ── 3 Lessons ──────────────────────────────────────────────────────
        for i in range(1, 4):
            cls.env["education.lms.lesson"].create({
                "course_id": cls.course.id,
                "title": "Lesson %d" % i,
                "lesson_type": "video",
                "sequence": i * 10,
            })

        # ── Quiz with 2 questions ──────────────────────────────────────────
        cls.quiz = cls.env["edu.lms.quiz"].create({
            "course_id": cls.course.id,
            "title": "Test Quiz",
            "pass_marks": 50.0,
            "time_limit_mins": 30,
            "max_attempts": 3,
        })
        cls.env["edu.lms.quiz.question"].create({
            "quiz_id": cls.quiz.id,
            "question_text": "What is 2 + 2?",
            "question_type": "mcq",
            "marks": 5.0,
            "sequence": 10,
        })
        cls.env["edu.lms.quiz.question"].create({
            "quiz_id": cls.quiz.id,
            "question_text": "The sky is blue.",
            "question_type": "true_false",
            "correct_answer": "true",
            "marks": 5.0,
            "sequence": 20,
        })

    # ── Tests ──────────────────────────────────────────────────────────────

    def test_course_publish(self):
        """action_publish() should transition state to 'published'."""
        self.course.action_publish()
        self.assertEqual(
            self.course.state, "published",
            "Course state should be 'published' after action_publish()",
        )
        # Reset for other tests
        self.course.action_reset_draft()

    def test_lesson_count(self):
        """lesson_count computed field should equal 3."""
        self.assertEqual(
            self.course.lesson_count, 3,
            "lesson_count should be 3 after creating 3 lessons",
        )

    def test_enrollment_created(self):
        """Creating an LMS enrollment sets state=enrolled and completion_pct=0.0."""
        lms_enr = self.env["edu.lms.enrollment"].create({
            "student_id": self.enrollment.id,
            "course_id": self.course.id,
        })
        self.assertEqual(lms_enr.state, "enrolled")
        self.assertAlmostEqual(lms_enr.completion_pct, 0.0, places=2)

    def test_mark_complete(self):
        """action_mark_complete() sets state=completed and completion_pct=100.0."""
        lms_enr = self.env["edu.lms.enrollment"].create({
            "student_id": self.enrollment.id,
            "course_id": self.course.id,
        })
        lms_enr.action_mark_complete()
        self.assertEqual(lms_enr.state, "completed")
        self.assertAlmostEqual(lms_enr.completion_pct, 100.0, places=2)

    def test_duplicate_enrollment(self):
        """Creating a second LMS enrollment for the same student+course raises ValidationError."""
        self.env["edu.lms.enrollment"].create({
            "student_id": self.enrollment.id,
            "course_id": self.course.id,
        })
        with self.assertRaises(Exception):
            self.env["edu.lms.enrollment"].create({
                "student_id": self.enrollment.id,
                "course_id": self.course.id,
            })

    def test_quiz_attempt(self):
        """Quiz attempt with score=8.0 out of max 10 (>=50%) should be marked passed."""
        attempt = self.env["edu.lms.quiz.attempt"].create({
            "student_id": self.enrollment.id,
            "quiz_id": self.quiz.id,
            "score": 8.0,
        })
        # max_score = sum of marks = 5 + 5 = 10
        self.assertAlmostEqual(attempt.max_score, 10.0, places=2)
        # percentage = 8/10 * 100 = 80% >= 50% pass_marks
        self.assertTrue(
            attempt.passed,
            "Attempt with 80% should be marked passed (pass_marks=50%)",
        )
        self.assertAlmostEqual(attempt.percentage, 80.0, places=2)

    def test_quiz_question_count(self):
        """quiz.question_count computed field should equal 2."""
        self.assertEqual(
            self.quiz.question_count, 2,
            "question_count should be 2 after creating 2 questions",
        )
