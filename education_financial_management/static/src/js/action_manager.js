/** @odoo-module **/

import { registry } from "@web/core/registry";
import { BlockUI, unblockUI } from "@web/core/ui/block_ui";
import { download } from "@web/core/network/download";

console.log("Education XLSX handler loaded");

registry
    .category("ir.actions.report handlers")
    .add("education_xlsx", async (action) => {

        if (action.report_type !== "xlsx") {
            return false;
        }

        BlockUI();

        try {
            await download({
                url: "/xlsx_reports",
                data: action.data,
            });
        } finally {
            unblockUI();
        }

        return true;
    });