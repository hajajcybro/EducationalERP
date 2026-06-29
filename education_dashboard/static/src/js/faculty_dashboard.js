/** @odoo-module **/
/**
 * education_dashboard — Faculty Dashboard (OWL client action)
 * Personal teaching workload, rosters, attendance and upcoming exams.
 */
import { registry } from "@web/core/registry";
import { Component, onWillStart, useState } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

export class EduFacultyDashboard extends Component {
    static template = "education_dashboard.FacultyDashboard";
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
        this.state.data = await this.orm.call("edu.dashboard", "get_faculty_dashboard", [false]);
        this.state.loading = false;
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
    openClassStudents(classId) {
        this.action.doAction({
            type: "ir.actions.act_window",
            name: "Class Roster",
            res_model: "education.enrollment",
            views: [[false, "list"], [false, "form"]],
            domain: [["class_id", "=", classId], ["state", "=", "active"]],
            target: "current",
        });
    }
}

registry.category("actions").add("education_dashboard.faculty_dashboard", EduFacultyDashboard);
