# -*- coding: utf-8 -*-
"""
education_analytics — SQL read-only view models (S7-T09)
=========================================================
Four PostgreSQL views surfaced as Odoo models with _auto = False:
  - edu.analytics.enrollment.summary
  - edu.analytics.fee.collection
  - edu.analytics.attendance.rate
  - edu.analytics.exam.pass.rate
"""
from odoo import models, fields, tools


class EduAnalyticsEnrollmentSummary(models.Model):
    """Enrollment counts grouped by program + academic year."""

    _name = "edu.analytics.enrollment.summary"
    _description = "Enrollment Summary Analytics"
    _auto = False
    _rec_name = "program_name"
    _order = "program_name"

    program_name = fields.Char(string="Program", readonly=True)
    academic_year_name = fields.Char(string="Academic Year", readonly=True)
    total_enrolled = fields.Integer(string="Total Enrolled", readonly=True, aggregator="sum")
    active_count = fields.Integer(string="Active", readonly=True, aggregator="sum")
    graduated_count = fields.Integer(string="Graduated", readonly=True, aggregator="sum")

    def init(self):
        # Drop first: program_name switched from jsonb (raw translatable
        # column) to text, and CREATE OR REPLACE cannot change a column type.
        tools.drop_view_if_exists(self.env.cr, "edu_analytics_enrollment_summary")
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW edu_analytics_enrollment_summary AS (
                SELECT
                    ROW_NUMBER() OVER ()            AS id,
                    ep.name ->> 'en_US'             AS program_name,
                    ay.name                         AS academic_year_name,
                    COUNT(ee.id)                    AS total_enrolled,
                    COUNT(ee.id) FILTER (
                        WHERE ee.state = 'active'
                    )                               AS active_count,
                    COUNT(ee.id) FILTER (
                        WHERE ee.state = 'graduated'
                    )                               AS graduated_count
                FROM education_enrollment ee
                JOIN education_program ep
                    ON ep.id = ee.program_id
                JOIN education_academic_year ay
                    ON ay.id = ee.academic_year_id
                GROUP BY
                    ep.name ->> 'en_US',
                    ay.name
            )
        """)


class EduAnalyticsFeeCollection(models.Model):
    """Fee collection totals grouped by academic year + class."""

    _name = "edu.analytics.fee.collection"
    _description = "Fee Collection Analytics"
    _auto = False
    _rec_name = "academic_year_name"
    _order = "academic_year_name desc"

    academic_year_name = fields.Char(string="Academic Year", readonly=True)
    class_name = fields.Char(string="Class", readonly=True)
    total_invoiced = fields.Float(string="Total Invoiced", readonly=True, aggregator="sum")
    total_paid = fields.Float(string="Total Paid", readonly=True, aggregator="sum")
    total_outstanding = fields.Float(string="Total Outstanding", readonly=True, aggregator="sum")
    overdue_count = fields.Integer(string="Overdue Count", readonly=True, aggregator="sum")

    def init(self):
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW edu_analytics_fee_collection AS (
                SELECT
                    ROW_NUMBER() OVER ()            AS id,
                    ay.name                         AS academic_year_name,
                    ec.name                         AS class_name,
                    COALESCE(SUM(ee.total_fee), 0)  AS total_invoiced,
                    COALESCE(SUM(ee.amount_paid), 0) AS total_paid,
                    COALESCE(SUM(ee.amount_due), 0) AS total_outstanding,
                    COUNT(ee.id) FILTER (
                        WHERE ee.fee_state = 'overdue'
                    )                               AS overdue_count
                FROM education_enrollment ee
                JOIN education_academic_year ay
                    ON ay.id = ee.academic_year_id
                LEFT JOIN education_class ec
                    ON ec.id = ee.class_id
                WHERE ee.state != 'withdrawn'
                GROUP BY
                    ay.name,
                    ec.name
            )
        """)


class EduAnalyticsAttendanceRate(models.Model):
    """Attendance rate per class per academic year."""

    _name = "edu.analytics.attendance.rate"
    _description = "Attendance Rate Analytics"
    _auto = False
    _rec_name = "class_name"
    _order = "class_name"

    class_name = fields.Char(string="Class", readonly=True)
    academic_year_name = fields.Char(string="Academic Year", readonly=True)
    total_records = fields.Integer(string="Total Records", readonly=True, aggregator="sum")
    present_count = fields.Integer(string="Present", readonly=True, aggregator="sum")
    attendance_rate = fields.Float(string="Attendance Rate (%)", readonly=True, aggregator="avg")

    def init(self):
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW edu_analytics_attendance_rate AS (
                SELECT
                    ROW_NUMBER() OVER ()            AS id,
                    ec.name                         AS class_name,
                    ay.name                         AS academic_year_name,
                    COUNT(ea.id)                    AS total_records,
                    COUNT(ea.id) FILTER (
                        WHERE ea.state IN ('present', 'late')
                    )                               AS present_count,
                    CASE
                        WHEN COUNT(ea.id) = 0 THEN 0
                        ELSE ROUND(
                            COUNT(ea.id) FILTER (
                                WHERE ea.state IN ('present', 'late')
                            ) * 100.0 / COUNT(ea.id),
                            2
                        )
                    END                             AS attendance_rate
                FROM education_attendance ea
                JOIN education_class ec
                    ON ec.id = ea.class_id
                JOIN education_academic_year ay
                    ON ay.id = ea.academic_year_id
                GROUP BY
                    ec.name,
                    ay.name
            )
        """)


class EduAnalyticsExamPassRate(models.Model):
    """Exam pass / fail counts grouped by exam + class."""

    _name = "edu.analytics.exam.pass.rate"
    _description = "Exam Pass Rate Analytics"
    _auto = False
    _rec_name = "exam_name"
    _order = "exam_name"

    exam_name = fields.Char(string="Exam", readonly=True)
    exam_type = fields.Char(string="Exam Type", readonly=True)
    class_name = fields.Char(string="Class", readonly=True)
    total_students = fields.Integer(string="Total Students", readonly=True, aggregator="sum")
    passed_count = fields.Integer(string="Passed", readonly=True, aggregator="sum")
    failed_count = fields.Integer(string="Failed", readonly=True, aggregator="sum")
    pass_rate = fields.Float(string="Pass Rate (%)", readonly=True, aggregator="avg")

    def init(self):
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW edu_analytics_exam_pass_rate AS (
                SELECT
                    ROW_NUMBER() OVER ()            AS id,
                    ex.name                         AS exam_name,
                    ex.exam_type                    AS exam_type,
                    ec.name                         AS class_name,
                    COUNT(er.id)                    AS total_students,
                    COUNT(er.id) FILTER (
                        WHERE er.pass_fail = 'pass'
                    )                               AS passed_count,
                    COUNT(er.id) FILTER (
                        WHERE er.pass_fail = 'fail'
                    )                               AS failed_count,
                    CASE
                        WHEN COUNT(er.id) = 0 THEN 0
                        ELSE ROUND(
                            COUNT(er.id) FILTER (
                                WHERE er.pass_fail = 'pass'
                            ) * 100.0 / COUNT(er.id),
                            2
                        )
                    END                             AS pass_rate
                FROM edu_exam_result er
                JOIN edu_exam ex
                    ON ex.id = er.exam_id
                LEFT JOIN education_class ec
                    ON ec.id = er.class_id
                GROUP BY
                    ex.name,
                    ex.exam_type,
                    ec.name
            )
        """)
