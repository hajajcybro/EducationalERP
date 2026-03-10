/** @odoo-module **/
import { registry } from "@web/core/registry";
import { BlockUI } from "@web/core/ui/block_ui";
import { download } from "@web/core/network/download";
console.log("loaded")

registry.category("ir.actions.report handlers").add("xlsx", async(action)=> {
    console.log("action",action.report_type);
    if (action.report_type === 'xlsx') {
        BlockUI;
        await download({
            url: '/xlsx_reports',
            data: action.data,
            complete: () => unblockUI,
            error: (error) => self.call('crash_manager', 'rpc_error', error),
        });
        return true
        }
    });
