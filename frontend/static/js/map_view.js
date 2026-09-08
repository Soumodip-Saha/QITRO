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
    this.incidentLayers = [];
    this.highlightLayer = null;
    this.routeColors = ['#06b6d4', '#a855f7', '#10b981', '#f59e0b', '#f43f5e', '#3b82f6'];
    this.hasOptimized = false;

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
    this.hasOptimized = false;
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

    this.incidentLayers.forEach(l => this.map.removeLayer(l));
    this.incidentLayers = [];

    this.clearHighlightEdge();
  }

  highlightEdge(u, v) {
    this.clearHighlightEdge();
    if (u === null || v === null || !this.nodeMarkers[u] || !this.nodeMarkers[v]) return;
    const uPos = this.nodeMarkers[u].getLatLng();
    const vPos = this.nodeMarkers[v].getLatLng();
    this.highlightLayer = L.polyline([[uPos.lat, uPos.lng], [vPos.lat, vPos.lng]], {
      color: '#38bdf8',
      weight: 6.5,
      opacity: 0.95,
      dashArray: '6, 6',
      lineJoin: 'round',
    }).addTo(this.map);

    // Snap highlight preview directly onto the real road
    fetch(`http://router.project-osrm.org/route/v1/driving/${uPos.lng},${uPos.lat};${vPos.lng},${vPos.lat}?overview=full&geometries=geojson`)
      .then(res => res.json())
      .then(data => {
        if (data?.routes?.[0]?.geometry?.coordinates && this.highlightLayer) {
          const roadPts = data.routes[0].geometry.coordinates.map(pt => [pt[1], pt[0]]);
          if (roadPts.length >= 2) this.highlightLayer.setLatLngs(roadPts);
        }
      })
      .catch(() => {});
  }

  clearHighlightEdge() {
    if (this.highlightLayer) {
      this.map.removeLayer(this.highlightLayer);
      this.highlightLayer = null;
    }
  }

  renderRoadNetwork(network) {
    this.clearAll();

    const nodeMap = {};
    network.nodes.forEach(n => {
      nodeMap[n.id] = n;
    });

    // 1. Draw Edges ONLY if 1st optimization has not yet run
    // ("Remove the imaginary lines after the 1st optimization")
    if (!this.hasOptimized && network.edges) {
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
          weight: 2.0,
          opacity: 0.5,
          dashArray: '3, 6',
        }).addTo(this.map);

        line.bindPopup(`
          <div style="font-size:0.8rem; color:#111; min-width:180px;">
            <strong>Corridor: ${uNode.name || uNode.id} &harr; ${vNode.name || vNode.id}</strong><br>
            Distance: ${e.distance_km} km | Speed Limit: ${e.speed_limit_kmh} km/h<br>
            Flow Time: ${Math.round(e.dynamic_time_sec || freeFlowSec)}s<br>
            <button onclick="window.openIncidentModalForEdge(${e.u}, ${e.v})" style="margin-top:6px; background:#ef4444; color:#fff; border:none; border-radius:4px; padding:4px 8px; font-size:0.75rem; cursor:pointer; font-weight:600; width:100%; display:block; text-align:center;">
              &#9888; Block This Road Portion
            </button>
          </div>
        `);
        this.edgeLayers.push(line);
      });
    }

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
        marker.bindPopup(`
          <div style="font-size:0.8rem; color:#111;">
            <strong>Central Logistics Hub</strong><br>${n.name || 'Majestic Central'}
            <button onclick="window.openIncidentModalForNode(${n.id})" style="margin-top:6px; background:#ef4444; color:#fff; border:none; border-radius:4px; padding:4px 8px; font-size:0.75rem; cursor:pointer; font-weight:600; width:100%; display:block; text-align:center;">
              &#9888; Block Highway to/from this Hub
            </button>
          </div>
        `);
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
            <button onclick="window.openIncidentModalForNode(${n.id})" style="margin-top:6px; background:#ef4444; color:#fff; border:none; border-radius:4px; padding:4px 8px; font-size:0.75rem; cursor:pointer; font-weight:600; width:100%; display:block; text-align:center;">
              &#9888; Block Highway to/from this City
            </button>
          </div>
        `);
      }
      this.nodeMarkers[n.id] = marker;
    });

    // 3. Draw Incidents
    this.renderIncidents(network.incidents, network);
  }

  renderIncidents(incidents, network) {
    Object.values(this.incidentMarkers).forEach(m => this.map.removeLayer(m));
    this.incidentMarkers = {};
    if (this.incidentLayers) {
      this.incidentLayers.forEach(l => this.map.removeLayer(l));
    }
    this.incidentLayers = [];

    if (!incidents || !Array.isArray(incidents) || incidents.length === 0 || !network || !network.nodes) return;

    const nodeMap = {};
    network.nodes.forEach(n => { nodeMap[n.id] = n; });

    incidents.forEach(inc => {
      if (!inc || inc.edge_u === undefined || inc.edge_v === undefined) return;

      const uNode = nodeMap[inc.edge_u];
      const vNode = nodeMap[inc.edge_v];
      if (!uNode || !vNode) return;

      const hasRealRoadGeo = inc.geojson_geometry && Array.isArray(inc.geojson_geometry) && inc.geojson_geometry.length > 0;
      let blockedLatLngs = [];
      let pinLat, pinLon;

      if (hasRealRoadGeo) {
        // Draw roadblock directly along the curved real-world road
        blockedLatLngs = inc.geojson_geometry.map(pt => [pt[0], pt[1]]);
        const midIdx = Math.floor(blockedLatLngs.length / 2);
        pinLat = blockedLatLngs[midIdx][0];
        pinLon = blockedLatLngs[midIdx][1];
      } else {
        // Fallback connecting nodes
        blockedLatLngs = [[uNode.lat, uNode.lon], [vNode.lat, vNode.lon]];
        pinLat = (uNode.lat + vNode.lat) / 2.0;
        pinLon = (uNode.lon + vNode.lon) / 2.0;
      }

      // Draw the blocked road corridor in bright glowing red ON THE ROAD
      const blockedLine = L.polyline(blockedLatLngs, {
        color: '#ef4444',
        weight: 6.5,
        opacity: 0.95,
        dashArray: '8, 8',
        lineJoin: 'round',
        lineCap: 'round',
      }).addTo(this.map);
      this.incidentLayers.push(blockedLine);

      const incIcon = L.divIcon({
        className: 'incident-pin',
        html: `<div style="background:#ef4444; width:28px; height:28px; border-radius:6px; border:2px solid #fff; box-shadow:0 0 16px #ef4444; display:flex; align-items:center; justify-content:center; font-size:15px; font-weight:bold; color:#fff; cursor:pointer;">&#9888;</div>`,
        iconSize: [28, 28],
        iconAnchor: [14, 14],
      });
      const incMarker = L.marker([pinLat, pinLon], { icon: incIcon, zIndexOffset: 2000 }).addTo(this.map);
      const uName = uNode.name || `Node ${inc.edge_u}`;
      const vName = vNode.name || `Node ${inc.edge_v}`;
      const incKey = inc.id || inc.incident_id || `${inc.edge_u}_${inc.edge_v}`;
      incMarker.bindPopup(`
        <div style="font-size:0.82rem; color:#111; min-width:190px;">
          <strong style="color:#ef4444; font-size:0.9rem;">&#9888; Roadblock Corridor</strong><br>
          <strong>Corridor:</strong> ${uName} &harr; ${vName}<br>
          <strong>Delay Added:</strong> +${Math.round(inc.delay_seconds / 60)} min (+${inc.delay_seconds}s)<br>
          <strong>Severity:</strong> ${(inc.severity * 100).toFixed(0)}%<br>
          <div style="margin-top:4px; font-style:italic; color:#64748b;">${inc.description || 'Active Congestion'}</div>
          <button onclick="window.removeSingleIncident('${incKey}')" style="margin-top:8px; width:100%; background:#dc2626; color:#fff; border:none; border-radius:4px; padding:4px 8px; font-size:0.75rem; cursor:pointer; font-weight:bold;">
            &#10005; Clear This Roadblock
          </button>
        </div>
      `);
      this.incidentMarkers[incKey] = incMarker;

      // If road geometry was not pre-computed, snap onto real road asynchronously via OSRM
      if (!hasRealRoadGeo) {
        fetch(`https://router.project-osrm.org/route/v1/driving/${uNode.lon},${uNode.lat};${vNode.lon},${vNode.lat}?overview=full&geometries=geojson`)
          .then(res => res.json())
          .then(data => {
            if (data?.routes?.[0]?.geometry?.coordinates) {
              const roadPts = data.routes[0].geometry.coordinates.map(pt => [pt[1], pt[0]]);
              if (roadPts.length >= 2) {
                blockedLine.setLatLngs(roadPts);
                const roadMid = roadPts[Math.floor(roadPts.length / 2)];
                incMarker.setLatLng(roadMid);
                inc.geojson_geometry = roadPts;
              }
            }
          })
          .catch(() => {});
      }
    });
  }

  renderRoutes(routes, network) {
    // 1. Remove the imaginary lines after the 1st optimization
    this.hasOptimized = true;
    this.edgeLayers.forEach(l => this.map.removeLayer(l));
    this.edgeLayers = [];

    // Clear old polylines
    this.routePolylines.forEach(p => this.map.removeLayer(p));
    this.routePolylines = [];

    const nodeMap = {};
    network.nodes.forEach(n => { nodeMap[n.id] = n; });

    routes.forEach((r, idx) => {
      if (!r.customer_ids || r.customer_ids.length === 0) return;

      const color = this.routeColors[idx % this.routeColors.length];
      const latlngs = [];
      const hasRealRoadGeo = r.geojson_geometry && Array.isArray(r.geojson_geometry) && r.geojson_geometry.length > 0;

      if (hasRealRoadGeo) {
        // Render high-precision real-world road curvature from OSRM Route API
        r.geojson_geometry.forEach(pt => {
          if (Array.isArray(pt) && pt.length >= 2) {
            latlngs.push([pt[0], pt[1]]);
          }
        });
      } else if (r.detailed_node_path && r.detailed_node_path.length > 0) {
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

      // Build road leg options for 1-click roadblock injection directly from this route
      let legsOptionsHtml = '';
      if (r.detailed_node_path && r.detailed_node_path.length >= 2) {
        const addedLegs = new Set();
        for (let i = 0; i < r.detailed_node_path.length - 1; i++) {
          const u = r.detailed_node_path[i];
          const v = r.detailed_node_path[i + 1];
          const canonical = u < v ? `${u}_${v}` : `${v}_${u}`;
          if (addedLegs.has(canonical)) continue;
          addedLegs.add(canonical);
          const uName = nodeMap[u]?.name || `Node ${u}`;
          const vName = nodeMap[v]?.name || `Node ${v}`;
          legsOptionsHtml += `<option value="${u}_${v}">${uName} ↔ ${vName}</option>`;
        }
      }

      const polyline = L.polyline(latlngs, {
        color: color,
        weight: 4.5,
        opacity: 0.92,
        lineJoin: 'round',
        lineCap: 'round',
      }).addTo(this.map);

      polyline.bindPopup(`
        <div style="font-size:0.85rem; color:#111; min-width:230px;">
          <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:4px;">
            <strong style="color:${color}; font-size:0.95rem;">Route #${r.vehicle_id}</strong>
            ${hasRealRoadGeo ? '<span style="background:#10b981; color:#fff; font-size:10px; font-weight:bold; padding:2px 6px; border-radius:3px;">OSRM Real Roads</span>' : ''}
          </div>
          Distance: <strong>${r.total_distance_km} km</strong><br>
          Travel Time: <strong>${Math.round(r.total_travel_time_sec / 60)} min</strong> (${r.total_travel_time_sec}s)<br>
          Stops: ${r.customer_ids.length} | Load: ${r.total_load} units<br>
          CO2: ${r.co2_kg} kg | Fuel: ${r.fuel_liters} L
          ${legsOptionsHtml ? `
            <div style="margin-top:8px; border-top:1px solid #e2e8f0; padding-top:6px;">
              <label style="font-size:0.72rem; font-weight:700; color:#ef4444; display:block; margin-bottom:3px;">
                &#9888; Block a Road Leg on this Route:
              </label>
              <select id="routeLegSelect_${r.vehicle_id}" style="width:100%; font-size:0.75rem; padding:3px 4px; border-radius:4px; border:1px solid #cbd5e1; background:#fff; color:#1e293b;">
                ${legsOptionsHtml}
              </select>
              <button onclick="window.injectRoadblockFromRouteSelect(${r.vehicle_id})" style="margin-top:6px; width:100%; background:#ef4444; color:#fff; border:none; border-radius:4px; padding:5px 8px; font-size:0.75rem; font-weight:bold; cursor:pointer;">
                &#9888; Block Selected Road Leg
              </button>
            </div>
          ` : ''}
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
