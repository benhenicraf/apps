frappe.ui.form.on("Wialon API Configuration", {
    refresh: function (frm) {
        // Add "Test API Connection" button
        // frm.add_custom_button("Test API Connection", function () {
        //     frappe.call({
        //         method: "components_core.api.wialon_auth.authenticate",
        //         callback: function (response) {
        //             if (response.message.success) {
        //                 frappe.msgprint("Wialon API Connected Successfully!", "Success");
        //             } else {
        //                 frappe.msgprint("Failed to Connect: " + response.message.error, "Error");
        //             }
        //         }
        //     });
        // });

        // Auto-refresh session status every 10 minutes
        setInterval(function () {
            frappe.call({
                method: "components_core.api.wialon_auth.get_valid_session",
                callback: function (response) {
                    if (!response.message) {
                        frappe.msgprint("Wialon Session Expired. Please Re-authenticate.", "Warning");
                    }
                }
            });
        }, 600000); // 10 minutes
    }
});
