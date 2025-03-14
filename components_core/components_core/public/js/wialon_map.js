frappe.provide("frappe.wialon_map");

frappe.wialon_map.Map = class WialonMap {
    constructor(options) {
        this.map_container = options.map_container || "#map";
        this.markers = new Map();
        this.initialize_map();
        this.connect_websocket();
    }

    initialize_map() {
        this.map = L.map(this.map_container).setView([0, 0], 2);
        L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
            attribution: "© OpenStreetMap contributors"
        }).addTo(this.map);
    }

    connect_websocket() {
        let ws = new WebSocket("wss://your-websocket-server/wialon");
        ws.onmessage = (event) => {
            let data = JSON.parse(event.data);
            this.update_markers(data.units);
        };
    }

    update_markers(units) {
        let unit_ids = new Set();
        units.forEach(unit => {
            unit_ids.add(unit.unit_id);
            if (this.markers.has(unit.unit_id)) {
                this.markers.get(unit.unit_id).setLatLng([unit.latitude, unit.longitude]);
            } else {
                let marker = L.marker([unit.latitude, unit.longitude])
                    .bindPopup(`${unit.name}<br>Speed: ${unit.speed} km/h<br>Last Updated: ${unit.last_updated}`)
                    .addTo(this.map);
                this.markers.set(unit.unit_id, marker);
            }
        });

        // Remove markers for disconnected units
        this.markers.forEach((marker, id) => {
            if (!unit_ids.has(id)) {
                this.map.removeLayer(marker);
                this.markers.delete(id);
            }
        });
    }
};

// Initialize map on page load
$(document).ready(function () {
    window.cur_map = new frappe.wialon_map.Map({ map_container: "map" });
});










// frappe.provide("frappe.wialon_map");

// frappe.wialon_map.Map = class WialonMap {
//     constructor(options) {
//         this.map_container = options.map_container || "#map";
//         this.markers = [];
//         this.initialize_map();
//         this.load_positions();
//     }

//     initialize_map() {
//         this.map = L.map(this.map_container).setView([0, 0], 2);
//         L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
//             attribution: "© OpenStreetMap contributors"
//         }).addTo(this.map);
//         // Update lat/lng dynamically on map move
//         this.map.on('move', () => {
//             const center = this.map.getCenter();
//             $("#map-lat").text(center.lat.toFixed(4));
//             $("#map-lng").text(center.lng.toFixed(4));
//         });
//     }

//     load_positions() {
//         frappe.call({
//             method: "components_core.components_core.api.wialon_units.get_live_positions",
//             callback: (r) => {
//                 if (r.message && !r.message.error) {
//                     this.update_markers(r.message);
//                 } else {
//                     // Show error to user if fetching fails
//                     frappe.msgprint("Failed to load positions: " + (r.message.error || "Unknown error"));
//                     console.error("Failed to load positions:", r.message.error);
//                 }
//             }
//         });
//     }

//     update_markers(units) {
//         // Clear existing markers
//         this.markers.forEach(marker => this.map.removeLayer(marker));
//         this.markers = units.map(unit => {
//             return L.marker([unit.latitude, unit.longitude])
//                 .addTo(this.map)
//                 .bindPopup(`${unit.name}<br>Speed: ${unit.speed} km/h<br>Last Updated: ${unit.last_updated}`);
//         });
//         if (this.markers.length > 0) {
//             const group = new L.featureGroup(this.markers);
//             this.map.fitBounds(group.getBounds());
//         } else {
//             // Inform user if no units are available
//             frappe.msgprint("No units available to display.");
//         }
//     }

//     fitToMarkers() {
//         if (this.markers.length > 0) {
//             const group = new L.featureGroup(this.markers);
//             this.map.fitBounds(group.getBounds());
//         }
//     }

//     toggleFullscreen() {
//         if (!document.fullscreenElement) {
//             this.map.getContainer().requestFullscreen();
//         } else {
//             document.exitFullscreen();
//         }
//     }
// };

// // Initialize map on page load
// $(document).ready(function() {
//     window.cur_map = new frappe.wialon_map.Map({ map_container: "map" });
// });









// // wialon_map.js
// frappe.provide("frappe.wialon_map");

// frappe.wialon_map.Map = class WialonMap {
//     constructor(options) {
//         this.map_container = options.map_container || "#map";
//         this.markers = [];
//         this.initialize_map();
//         this.load_positions();
//     }

//     initialize_map() {
//         // Grok modified: Initialize Leaflet map
//         this.map = L.map(this.map_container).setView([0, 0], 2);
//         L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
//             attribution: "© OpenStreetMap contributors"
//         }).addTo(this.map);
//     }

//     load_positions() {
//         // Grok modified: Fetch live positions from backend
//         frappe.call({
//             method: "components_core.components_core.api.wialon_units.get_live_positions",
//             callback: (r) => {
//                 if (r.message && !r.message.error) {
//                     this.update_markers(r.message);
//                 } else {
//                     console.error("Failed to load positions:", r.message.error);
//                 }
//             }
//         });
//     }

//     update_markers(units) {
//         // Grok modified: Add or update markers on the map
//         this.markers.forEach(marker => this.map.removeLayer(marker));
//         this.markers = units.map(unit => {
//             return L.marker([unit.latitude, unit.longitude])
//                 .addTo(this.map)
//                 .bindPopup(`${unit.name}<br>Speed: ${unit.speed} km/h<br>Last Updated: ${unit.last_updated}`);
//         });
//         if (this.markers.length > 0) {
//             const group = new L.featureGroup(this.markers);
//             this.map.fitBounds(group.getBounds());
//         }
//     }

//     fitToMarkers() {
//         // Grok modified: Fit map to all markers
//         if (this.markers.length > 0) {
//             const group = new L.featureGroup(this.markers);
//             this.map.fitBounds(group.getBounds());
//         }
//     }

//     toggleFullscreen() {
//         // Grok modified: Toggle fullscreen mode
//         if (!document.fullscreenElement) {
//             this.map.getContainer().requestFullscreen();
//         } else {
//             document.exitFullscreen();
//         }
//     }
// };

// // Grok modified: Initialize map on document ready
// $(document).ready(function() {
//     window.cur_map = new frappe.wialon_map.Map({ map_container: "map" });
// });










// // class WialonMapController {
// //     constructor(wrapper) {
// //         this.wrapper = wrapper;
// //         this.markers = {};
// //         this.initMap();
// //         this.initRealtime();
// //     }

// //     initMap() {
// //         this.map = L.map('map').setView([11.394769, 103.7475316], 10);
// //         L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png').addTo(this.map);
// //     }

// //     initRealtime() {
// //         frappe.realtime.on('unit_position_update', (data) => {
// //             this.updateUnitMarker(data);
// //         });

// //         setInterval(() => this.fetchLivePositions(), 5000);
// //     }

// //     fetchLivePositions() {
// //         fetch('/api/method/components_core.api.wialon_units.get_live_positions')
// //             .then(response => response.json())
// //             .then(data => {
// //                 if (data.message.length > 0) {
// //                     data.message.forEach(unit => this.updateUnitMarker(unit));
// //                 }
// //             });
// //     }

// //     updateUnitMarker(unit) {
// //         if (this.markers[unit.unit_id]) {
// //             this.markers[unit.unit_id].setLatLng([unit.latitude, unit.longitude]);
// //         } else {
// //             this.markers[unit.unit_id] = L.marker([unit.latitude, unit.longitude])
// //                 .bindPopup(`<b>${unit.name}</b><br>Speed: ${unit.speed} km/h`)
// //                 .addTo(this.map);
// //         }
// //     }
// // }
