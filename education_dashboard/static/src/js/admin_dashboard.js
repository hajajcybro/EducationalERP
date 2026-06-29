/** @odoo-module **/
/**
 * education_dashboard — Admin Dashboard (OWL client action)
 * Live institution-wide KPIs, charts and quick actions.
 */
import { registry } from "@web/core/registry";
import { Component, onWillStart, useState } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

export class EduAdminDashboard extends Component {
    static template = "education_dashboard.AdminDashboard";
    static props = ["*"];

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.state = useState({ loading: true, data: {} });
        onWillStart(async () => {
            await this.load();
        });
    }

    async load() {
        this.state.loading = true;
        this.state.data = await this.orm.call("edu.dashboard", "get_admin_dashboard", []);
        this.state.loading = false;
    }

    /** Bars scaled to the largest value in the series. */
    _bars(series) {
        const max = Math.max(1, ...series.map((r) => r.value));
        return series.map((r) => ({ ...r, pct: Math.round((r.value / max) * 100) }));
    }
    get programBars() {
        return this._bars(this.state.data.by_program || []);
    }
    get funnelBars() {
        return this._bars(this.state.data.funnel || []);
    }

    openList(name, model, domain) {
        this.action.doAction({
            type: "ir.actions.act_window",
            name,
            res_model: model,
            views: [[false, "list"], [false, "form"]],
            domain: domain || [],
            target: "current",
        });
    }
    openRecord(model, resId) {
        this.action.doAction({
            type: "ir.actions.act_window",
            res_model: model,
            res_id: resId,
            views: [[false, "form"]],
            target: "current",
        });
    }

    onStudents() { this.openList("Students", "education.enrollment", [["state", "=", "active"]]); }
    onApplications() { this.openList("Pending Applications", "education.application", [["state", "=", "submitted"]]); }
    onExams() { this.openList("Exams", "edu.exam", [["state", "in", ["scheduled", "ongoing"]]]); }
    onFaculty() { this.openList("Faculty", "education.faculty", []); }
    onPrograms() { this.openList("Programs", "education.program", []); }
    onClasses() { this.openList("Classes", "education.class", []); }
    onFees() {
        // Drill into the related unpaid fee invoices
        this.openList("Outstanding Fee Invoices", "account.move", [
            ["move_type", "=", "out_invoice"],
            ["enrollment_id", "!=", false],
            ["payment_state", "in", ["not_paid", "partial"]],
        ]);
    }
}

registry.category("actions").add("education_dashboard.admin_dashboard", EduAdminDashboard);
