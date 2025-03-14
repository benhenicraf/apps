frappe.listview_settings['Wialon Notification'] = {
    add_fields: ["template_id", "unit_id", "event_time", "type"],
    button: {
        show: function(doc) {
            return true;
        },
        get_label: function() {
            return __("Fetch Now");
        },
        get_description: function() {
            return __("Fetch Wialon notifications now");
        },
        action: function() {
            frappe.call({
                method: "wialon_notifications.api.wialon_notifications.fetch_and_save_notifications",
                callback: function(r) {
                    if (r.exc) {
                        frappe.msgprint("Failed to fetch notifications. Check logs for details.");
                    } else {
                        frappe.msgprint("Notifications fetched successfully!");
                        frappe.ui.toolbar.clear_cache();
                    }
                }
            });
        }
    }
};