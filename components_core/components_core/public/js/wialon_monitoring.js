document.addEventListener("DOMContentLoaded", () => {
    const map = L.map('map').setView([1.3521, 103.8198], 12); // Default to Singapore

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap'
    }).addTo(map);

    fetchUnits(map);
    setInterval(() => fetchUnits(map), 30000);  // Refresh every 30 seconds
});

function fetchUnits(map) {
    frappe.call({
        method: "components_core.api.wialon_fetch.fetch_wialon_units",
        callback: function(r) {
            if (r.message.units) {
                populateUnits(r.message.units, map);
            }
        }
    });
}

let markers = {};

function populateUnits(units, map) {
    let unitList = document.getElementById('unitList');
    unitList.innerHTML = '';

    units.forEach(unit => {
        let li = document.createElement('li');
        li.textContent = `${unit.name} (${unit.unit_id})`;
        li.onclick = () => {
            if(markers[unit.unit_id]){
                map.setView(markers[unit.unit_id].getLatLng(), 15);
                markers[unit.unit_id].openPopup();
            }
        };
        unitList.appendChild(li);

        if (markers[unit.unit_id]) {
            markers[unit.unit_id].setLatLng([unit.latitude, unit.longitude]);
        } else {
            markers[unit.unit_id] = L.marker([unit.latitude, unit.longitude])
                .addTo(map)
                .bindPopup(`<strong>${unit.name}</strong><br>ID: ${unit.unit_id}<br>Type: ${unit.unit_type}`);
        }
    });
}













// frappe.pages["wialon-monitoring"].on_page_load = function(wrapper) {
//     frappe.ui.make_app_page({
//         parent: wrapper,
//         title: __("Live Equipment Monitoring"),
//         single_column: true
//     });
    
//     new WialonMapController(wrapper);
// };

// class WialonMapController {
//     constructor(wrapper) {
//         this.wrapper = wrapper;
//         this.markers = new Map();
//         this.initialize_map();
//         this.setup_realtime();
//     }

//     initialize_map() {
//         // Create map container
//         this.wrapper.html(`
//             <div class="map-container">
//                 <div id="wialon-map" style="height: 80vh;"></div>
//                 ${frappe.render_template("map_controls")}
//             </div>
//         `);

//         // Initialize map
//         this.map = L.map('wialon-map', {
//             zoomControl: false,
//             preferCanvas: true
//         }).setView([11.394769, 103.7475316], 10);

//         L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
//             attribution: '© OpenStreetMap contributors'
//         }).addTo(this.map);

//         L.control.zoom({ position: 'topright' }).addTo(this.map);
//         this.load_initial_data();
//     }

//     async load_initial_data() {
//         try {
//             const response = await frappe.call({
//                 method: "components_core.api.wialon_units.get_live_positions"
//             });
            
//             if (response.message && response.message.length) {
//                 this.update_markers(response.message);
//             }
//         } catch (error) {
//             console.error("Initial load failed:", error);
//         }
//     }

//     setup_realtime() {
//         // Real-time updates every 5 seconds
//         this.update_interval = setInterval(() => this.update_positions(), 5000);
        
//         // Cleanup on page destroy
//         $(this.wrapper).on('destroy', () => {
//             clearInterval(this.update_interval);
//             this.map.remove();
//         });
//     }

//     async update_positions() {
//         try {
//             const response = await frappe.call({
//                 method: "components_core.api.wialon_units.get_live_positions"
//             });
            
//             if (response.message) {
//                 this.update_markers(response.message);
//             }
//         } catch (error) {
//             console.error("Position update failed:", error);
//         }
//     }

//     update_markers(units) {
//         const current_ids = new Set();
        
//         units.forEach(unit => {
//             current_ids.add(unit.unit_id);
            
//             if (this.markers.has(unit.unit_id)) {
//                 this.update_existing_marker(unit);
//             } else {
//                 this.create_new_marker(unit);
//             }
//         });

//         // Remove old markers
//         this.markers.forEach((marker, id) => {
//             if (!current_ids.has(id)) {
//                 this.map.removeLayer(marker);
//                 this.markers.delete(id);
//             }
//         });
//     }

//     create_new_marker(unit) {
//         const marker = L.marker([unit.latitude, unit.longitude], {
//             icon: L.divIcon({
//                 className: 'equipment-marker',
//                 html: `<div class="marker-content">
//                          <div class="marker-icon"></div>
//                          <div class="speed-badge">${Math.round(unit.speed)}km/h</div>
//                        </div>`
//             })
//         }).bindPopup(this.create_popup_content(unit));
        
//         marker.addTo(this.map);
//         this.markers.set(unit.unit_id, marker);
//     }

//     update_existing_marker(unit) {
//         const marker = this.markers.get(unit.unit_id);
//         marker.setLatLng([unit.latitude, unit.longitude]);
//         marker.setPopupContent(this.create_popup_content(unit));
//     }

//     create_popup_content(unit) {
//         return `<div class="wialon-popup">
//                   <h5>${unit.name}</h5>
//                   <div class="small text-muted">ID: ${unit.unit_id}</div>
//                   <hr>
//                   <div>Last Update: ${unit.last_updated}</div>
//                   <div>Speed: ${Math.round(unit.speed)} km/h</div>
//                 </div>`;
//     }
// }