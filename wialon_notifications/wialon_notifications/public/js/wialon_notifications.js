frappe.ready(() => {
    function fetchNotifications() {
        frappe.call({
            method: "wialon_notifications.api.wialon_fetch.get_notifications",
            callback: (response) => {
                let tableBody = document.getElementById("notification-list");
                tableBody.innerHTML = "";

                if (response.message && response.message.length > 0) {
                    response.message.forEach(notif => {
                        let row = `<tr>
                            <td>${notif.t}</td>
                            <td>${new Date(notif.tm * 1000).toLocaleString()}</td>
                            <td>${notif.p}</td>
                        </tr>`;
                        tableBody.innerHTML += row;
                    });
                } else {
                    tableBody.innerHTML = "<tr><td colspan='3'>No notifications</td></tr>";
                }
            }
        });
    }

    // Fetch notifications every 10 seconds
    fetchNotifications();
    setInterval(fetchNotifications, 10000);
});
