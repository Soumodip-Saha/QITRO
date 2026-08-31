/**
 * Leaflet Road Network & Dynamic Vehicle Fleet Map View
 */

class MapView {
  constructor(elementId) {
    this.elementId = elementId;
    this.map = null;
    this.nodeMarkers = {};
    this.edgeLayers = [];
    this.routePolylines = [];
    this.vehicleMarkers = {};
    this.incidentMarkers = {};
    this.routeColors = ['#06b6d4', '#a855f7', '#10b981', '#f59e0b', '#f43f5e', '#3b82f6'];

    this.initMap();
  }

  initMap() {
    this.map = L.map(this.elementId, {
      center: [12.9716, 77.5946],
      zoom: 12,
      zoomControl: true,
    });

    // CARTO Dark Matter tile layer with API key
    L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png?key=cb1_2h0d_1_0a7406526f817a7a3f138582', {
      attribution: '&copy; OpenStreetMap contributors &copy; CARTO',
      subdomains: 'abcd',
      maxZoom: 19,
    }).addTo(this.map);
  }

  setCityView(lat, lon, zoom = 12) {
    this.map.setView([lat, lon], zoom);
  }

  clearAll() {
    Object.values(this.nodeMarkers).forEach(m => this.map.removeLayer(m));
    this.nodeMarkers = {};

    this.edgeLayers.forEach(l => this.map.removeLayer(l));
    this.edgeLayers = [];

    this.routePolylines.forEach(p => this.map.removeLayer(p));
    this.routePolylines = [];

    Object.values(this.vehicleMarkers).forEach(v => this.map.removeLayer(v));
    this.vehicleMarkers = {};

    Object.values(this.incidentMarkers).forEach(i => this.map.removeLayer(i));
    this.incidentMarkers = {};
  }

  renderRoadNetwork(network) {
    this.clearAll();

    const nodeMap = {};
    network.nodes.forEach(n => {
      nodeMap[n.id] = n;
    });

    // 1. Draw Edges
    network.edges.forEach(e => {
      const uNode = nodeMap[e.u];
      const vNode = nodeMap[e.v];
      if (!uNode || !vNode) return;

      const freeFlowSec = (e.distance_km * 1000) / ((e.speed_limit_kmh * 1000) / 3600);
      const congestionRatio = (e.dynamic_time_sec || freeFlowSec) / Math.max(1, freeFlowSec);

      let edgeColor = 'rgba(71, 85, 105, 0.4)'; // normal slate
      if (congestionRatio > 2.0) edgeColor = 'rgba(239, 68, 68, 0.7)'; // severe red
      else if (congestionRatio > 1.3) edgeColor = 'rgba(245, 158, 11, 0.6)'; // moderate yellow

      const line = L.polyline([[uNode.lat, uNode.lon], [vNode.lat, vNode.lon]], {
        color: edgeColor,
        weight: 2.5,
        opacity: 0.6,
        dashArray: '3, 6',
      }).addTo(this.map);

      line.bindPopup(`
        <div style="font-size:0.8rem; color:#111;">
          <strong>Edge: ${uNode.name || uNode.id} &harr; ${vNode.name || vNode.id}</strong><br>
          Distance: ${e.distance_km} km | Speed Limit: ${e.speed_limit_kmh} km/h<br>
          Capacity: ${e.capacity_vph} vph | Flow Time: ${Math.round(e.dynamic_time_sec || freeFlowSec)}s
        </div>
      `);
      this.edgeLayers.push(line);
    });

    // 2. Draw Nodes
    network.nodes.forEach(n => {
      let marker;
      if (n.is_depot) {
        // Depot Marker
        const depotIcon = L.divIcon({
          className: 'depot-pin',
          html: `<div style="background:#f59e0b; width:22px; height:22px; border-radius:50%; border:2px solid #fff; box-shadow:0 0 10px #f59e0b; display:flex; align-items:center; justify-content:center; font-size:11px; font-weight:bold; color:#000;">HUB</div>`,
          iconSize: [22, 22],
          iconAnchor: [11, 11],
        });
        marker = L.marker([n.lat, n.lon], { icon: depotIcon }).addTo(this.map);
        marker.bindPopup(`<strong>Central Logistics Hub</strong><br>${n.name || 'Majestic Central'}`);
      } else {
        // Customer Stop Marker
        const custIcon = L.divIcon({
          className: 'cust-pin',
          html: `<div style="background:#06b6d4; width:18px; height:18px; border-radius:50%; border:2px solid #fff; box-shadow:0 0 8px #06b6d4; display:flex; align-items:center; justify-content:center; font-size:9px; font-weight:bold; color:#000;">${n.id}</div>`,
          iconSize: [18, 18],
          iconAnchor: [9, 9],
        });
        marker = L.marker([n.lat, n.lon], { icon: custIcon }).addTo(this.map);
        const twStart = new Date(n.time_window_start * 1000).toISOString().substr(11, 5);
        const twEnd = new Date(n.time_window_end * 1000).toISOString().substr(11, 5);
        marker.bindPopup(`
          <div style="font-size:0.8rem; color:#111;">
            <strong>${n.name || 'Customer ' + n.id}</strong><br>
            Demand: ${n.demand} units<br>
            Time Window: ${twStart} - ${twEnd}<br>
            Service Time: ${Math.round(n.service_time / 60)} min
          </div>
        `);
      }
      this.nodeMarkers[n.id] = marker;
    });

    // 3. Draw Incidents
    if (network.incidents) {
      network.incidents.forEach(inc => {
        const uNode = nodeMap[inc.edge_u];
        const vNode = nodeMap[inc.edge_v];
        if (uNode && vNode) {
          const midLat = (uNode.lat + vNode.lat) / 2.0;
          const midLon = (uNode.lon + vNode.lon) / 2.0;
          const incIcon = L.divIcon({
            className: 'incident-pin',
            html: `<div style="background:#ef4444; width:22px; height:22px; border-radius:4px; border:2px solid #fff; box-shadow:0 0 12px #ef4444; display:flex; align-items:center; justify-content:center; font-size:12px; font-weight:bold; color:#fff;">&#9888;</div>`,
            iconSize: [22, 22],
            iconAnchor: [11, 11],
          });
          const incMarker = L.marker([midLat, midLon], { icon: incIcon }).addTo(this.map);
          incMarker.bindPopup(`
            <strong style="color:red;">Incident Blockage</strong><br>
            ${inc.description}<br>
            Severity: ${(inc.severity * 100).toFixed(0)}% | Delay: +${inc.delay_seconds}s
          `);
          this.incidentMarkers[inc.id] = incMarker;
        }
      });
    }
  }

  renderRoutes(routes, network) {
    // Clear old polylines
    this.routePolylines.forEach(p => this.map.removeLayer(p));
    this.routePolylines = [];

    const nodeMap = {};
    network.nodes.forEach(n => { nodeMap[n.id] = n; });

    routes.forEach((r, idx) => {
      if (!r.customer_ids || r.customer_ids.length === 0) return;

      const color = this.routeColors[idx % this.routeColors.length];
      const latlngs = [];

      if (r.detailed_node_path && r.detailed_node_path.length > 0) {
        r.detailed_node_path.forEach(nid => {
          if (nodeMap[nid]) {
            latlngs.push([nodeMap[nid].lat, nodeMap[nid].lon]);
          }
        });
      } else {
        // Fallback connecting stops
        latlngs.push([nodeMap[network.nodes[0].id].lat, nodeMap[network.nodes[0].id].lon]);
        r.stops.forEach(s => {
          if (nodeMap[s.node_id]) latlngs.push([nodeMap[s.node_id].lat, nodeMap[s.node_id].lon]);
        });
        latlngs.push([nodeMap[network.nodes[0].id].lat, nodeMap[network.nodes[0].id].lon]);
      }

      const polyline = L.polyline(latlngs, {
        color: color,
        weight: 4.5,
        opacity: 0.9,
        lineJoin: 'round',
      }).addTo(this.map);

      polyline.bindPopup(`
        <div style="font-size:0.85rem; color:#111;">
          <strong style="color:${color};">Route #${r.vehicle_id}</strong><br>
          Distance: ${r.total_distance_km} km<br>
          Travel Time: ${Math.round(r.total_travel_time_sec / 60)} min<br>
          Stops: ${r.customer_ids.length} | Load: ${r.total_load} units<br>
          CO2: ${r.co2_kg} kg | Fuel: ${r.fuel_liters} L
        </div>
      `);
      this.routePolylines.push(polyline);
    });
  }

  updateVehicleAgents(agents) {
    agents.forEach(a => {
      let marker = this.vehicleMarkers[a.vehicle_id];
      const color = this.routeColors[(a.vehicle_id - 1) % this.routeColors.length];

      if (!marker) {
        const vIcon = L.divIcon({
          className: `veh-pin-${a.vehicle_id}`,
          html: `<div style="background:${color}; width:24px; height:24px; border-radius:50%; border:2px solid #fff; box-shadow:0 0 12px ${color}; display:flex; align-items:center; justify-content:center; font-size:10px; font-weight:bold; color:#000;">V${a.vehicle_id}</div>`,
          iconSize: [24, 24],
          iconAnchor: [12, 12],
        });
        marker = L.marker([a.lat, a.lon], { icon: vIcon, zIndexOffset: 1000 }).addTo(this.map);
        this.vehicleMarkers[a.vehicle_id] = marker;
      } else {
        marker.setLatLng([a.lat, a.lon]);
      }

      marker.bindTooltip(`
        <div style="font-size:0.75rem;">
          <strong>Vehicle ${a.vehicle_id} [${a.status}]</strong><br>
          Speed: ${a.speed_kmh} km/h | Dist: ${a.distance_km} km<br>
          CO2: ${a.co2_kg} kg | Left Stops: ${a.remaining_count}
        </div>
      `, { permanent: false, direction: 'top' });
    });
  }
}
