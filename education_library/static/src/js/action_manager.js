/** @odoo-module **/
import { registry } from "@web/core/registry";
import { download } from "@web/core/network/download";

registry.category("ir.actions.report handlers").add("xlsx", async (action) => {
    if (action.report_type === 'xlsx') {
        try {
            await download({
                url: '/library_xlsx_reports',
                data: action.data,
            });

            return true;
        } catch (error) {
            console.error('Error generating XLSX report:', error);
            throw error;
        }
    }
});