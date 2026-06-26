/** @odoo-module **/
/**
 * education_analytics — OWL Dashboard placeholder components
 * ===========================================================
 * Registers client action tags consumed by the ir.actions.client records
 * in analytics_views.xml.
 */

import { registry } from "@web/core/registry";
import { Component, xml } from "@odoo/owl";

// ── Admin Dashboard ────────────────────────────────────────────────────────

class AdminDashboard extends Component {
    static template = xml`
        <div class="o_edu_dashboard_placeholder d-flex flex-column align-items-center justify-content-center"
             style="min-height:60vh;">
            <i class="fa fa-tachometer fa-4x text-muted mb-3"></i>
            <h3 class="text-muted">Admin Dashboard</h3>
            <p class="text-muted">KPI cards and fee collection chart — coming soon.</p>
        </div>
    `;
    static props = {};
}
registry.category("actions").add("edu_analytics.AdminDashboard", AdminDashboard);

// ── Teacher Dashboard ──────────────────────────────────────────────────────

class TeacherDashboard extends Component {
    static template = xml`
        <div class="o_edu_dashboard_placeholder d-flex flex-column align-items-center justify-content-center"
             style="min-height:60vh;">
            <i class="fa fa-graduation-cap fa-4x text-muted mb-3"></i>
            <h3 class="text-muted">Teacher Dashboard</h3>
            <p class="text-muted">My classes, attendance pending, upcoming exams — coming soon.</p>
        </div>
    `;
    static props = {};
}
registry.category("actions").add("edu_analytics.TeacherDashboard", TeacherDashboard);

// ── Student Dashboard ──────────────────────────────────────────────────────

class StudentDashboard extends Component {
    static template = xml`
        <div class="o_edu_dashboard_placeholder d-flex flex-column align-items-center justify-content-center"
             style="min-height:60vh;">
            <i class="fa fa-user fa-4x text-muted mb-3"></i>
            <h3 class="text-muted">Student Dashboard</h3>
            <p class="text-muted">Grades, attendance, fee status, course progress — coming soon.</p>
        </div>
    `;
    static props = {};
}
registry.category("actions").add("edu_analytics.StudentDashboard", StudentDashboard);

// ── Accountant Dashboard ───────────────────────────────────────────────────

class AccountantDashboard extends Component {
    static template = xml`
        <div class="o_edu_dashboard_placeholder d-flex flex-column align-items-center justify-content-center"
             style="min-height:60vh;">
            <i class="fa fa-money fa-4x text-muted mb-3"></i>
            <h3 class="text-muted">Accountant Dashboard</h3>
            <p class="text-muted">Collection vs target, overdue report — coming soon.</p>
        </div>
    `;
    static props = {};
}
registry.category("actions").add("edu_analytics.AccountantDashboard", AccountantDashboard);
