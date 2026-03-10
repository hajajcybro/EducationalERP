/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";

publicWidget.registry.PortalAttendanceCalendar = publicWidget.Widget.extend({
    selector: "#attendance_calendar",
    async start() {
        await this._super(...arguments);
        const calendarEl = this.el;
        const calendar = new FullCalendar.Calendar(calendarEl, {
            initialView: "dayGridMonth",
            height: 650,
            events: async function(fetchInfo, successCallback, failureCallback) {
                try {
                    const response = await fetch("/my/my-attendance/events", {
                        method: "POST",
                        headers: {
                            "Content-Type": "application/json",
                        },
                        body: JSON.stringify({
                            jsonrpc: "2.0",
                            method: "call",
                            params: {},
                            id: 1,
                        }),
                    });
                    const result = await response.json();
                    successCallback(result.result);
                } catch (error) {
                    failureCallback(error);
                }
            },
        });
        calendar.render();
    },
});
