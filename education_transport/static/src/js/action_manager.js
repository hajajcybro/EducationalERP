/** @odoo-module **/

import { registry } from "@web/core/registry";
import { BlockUI } from "@web/core/ui/block_ui";
import { download } from "@web/core/network/download";

console.log("XLSX report handler loaded");

registry.category("ir.actions.report.handlers").add(
    "xlsx",
    async (action, options, env) => {
        if (action.report_type !== "xlsx") {
            return false;
        }
        try {
            BlockUI.block();

            await download({
                url: "/xlsx_reports",
                data: action.data,
            });

        } catch (error) {
            env.services.crash_manager.rpc_error(error);
        } finally {
            BlockUI.unblock();
        }
        return true;
    }
);
