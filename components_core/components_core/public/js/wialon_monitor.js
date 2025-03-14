frappe.pages['wialon_monitoring'].on_page_load = function(wrapper) {
    let map = L.map('map').setView([1.3047249, 103.7477816], 10);
    
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png').addTo(map);
    
    let markers = {};

    function updateMarkers() {
        frappe.call({
            method: "components_core.api.wialon_units.get_live_positions",
            callback: function(response) {
                if (response.message) {
                    response.message.forEach(unit => {
                        let latlng = [unit.latitude, unit.longitude];

                        if (markers[unit.unit_id]) {
                            markers[unit.unit_id].setLatLng(latlng);
                        } else {
                            markers[unit.unit_id] = L.marker(latlng)
                                .bindPopup(`<b>${unit.name}</b><br>Speed: ${unit.speed} km/h`)
                                .addTo(map);
                        }
                    });
                }
            }
        });
    }

    updateMarkers();
    setInterval(updateMarkers, 5000);
};
