/**
 * QITRO Main Application Controller
 */

document.addEventListener('DOMContentLoaded', async () => {
  const mapView = new MapView('map');
  const quantumView = new QuantumView('quantumCanvas');
  const benchmarkView = new BenchmarkView('convergenceChart');

  let currentNetwork = null;
  let currentSolution = null;
  let simTimer = null;
  let isSimulating = false;

  // 1. Initialize City Graph
  async function loadCity(cityId) {
    try {
      const network = await API.getCityGraph(cityId);
      currentNetwork = network;
      mapView.renderRoadNetwork(network);
      updateRoadblockBadges();

      const presets = await API.getCityPresets();
      const cityMeta = presets.cities.find(c => c.id === cityId);
      if (cityMeta) {
        mapView.setCityView(cityMeta.center[0], cityMeta.center[1], cityMeta.zoom);
      }
    } catch (e) {
      console.error('Failed to load city graph:', e);
    }
  }

  await loadCity(document.getElementById('citySelect').value || 'india_national');

  // City Selector Change
  document.getElementById('citySelect').addEventListener('change', async (e) => {
    await loadCity(e.target.value);
  });

  // 2. Optimize Button Handler
  document.getElementById('btnOptimize').addEventListener('click', async () => {
    const btn = document.getElementById('btnOptimize');
    btn.disabled = true;
    btn.innerText = 'Quantum Optimizing...';

    const payload = {
      city_id: document.getElementById('citySelect').value,
      algorithm: document.getElementById('algoSelect').value,
      num_vehicles: parseInt(document.getElementById('fleetSize').value) || 3,
      vehicle_capacity: parseFloat(document.getElementById('vehicleCap').value) || 80.0,
      iterations: parseInt(document.getElementById('iterations').value) || 120,
      weather: document.getElementById('weatherSelect').value,
    };

    try {
      const res = await API.optimize(payload);
      currentSolution = res.solution;
      currentNetwork = res.network;
      updateRoadblockBadges();

      // Update Map & KPIs
      mapView.renderRoadNetwork(res.network);
      mapView.renderRoutes(res.solution.routes, res.network);

      // Update Metric Cards
      document.getElementById('kpiFitness').innerText = res.solution.fitness_score.toFixed(2);
      document.getElementById('kpiDistance').innerText = `${res.solution.total_distance_km} km`;
      document.getElementById('kpiTravelTime').innerText = `${Math.round(res.solution.total_travel_time_sec / 60)} min`;
      document.getElementById('kpiCO2').innerText = `${res.solution.total_co2_kg} kg`;
      document.getElementById('kpiCompTime').innerText = `${res.solution.computation_time_ms.toFixed(1)} ms`;

      // Update Convergence Chart
      if (res.solution.convergence_history && res.solution.convergence_history.length > 0) {
        benchmarkView.updateSingleRunConvergence(res.solution.algorithm_name, res.solution.convergence_history);
      }

      // Update Quantum Visualizer
      quantumView.updateQuantumState({
        alpha: 0.5,
        mbest_norm: 1.0,
        quantum_dispersion: 0.8,
      });

    } catch (e) {
      alert(`Optimization failed: ${e.message}`);
    } finally {
      btn.disabled = false;
      btn.innerHTML = '&#9889; Run Optimization';
    }
  });

  // 3. Benchmark Arena Handler
  document.getElementById('btnBenchmark').addEventListener('click', async () => {
    const btn = document.getElementById('btnBenchmark');
    btn.disabled = true;
    btn.innerText = 'Benchmarking Swarms...';

    const payload = {
      city_id: document.getElementById('citySelect').value,
      algorithms: ['QPSO', 'QGA', 'QSA', 'PSO', 'GA', 'SA', 'CLARKE_WRIGHT'],
      num_runs: 5,
      iterations: 80,
      num_vehicles: parseInt(document.getElementById('fleetSize').value) || 3,
      vehicle_capacity: parseFloat(document.getElementById('vehicleCap').value) || 80.0,
    };

    try {
      const res = await API.runBenchmark(payload);
      benchmarkView.updateMultiAlgorithmBenchmark(res);

      // Render best QPSO solution on map
      if (res.best_solutions && res.best_solutions.QPSO) {
        mapView.renderRoutes(res.best_solutions.QPSO.routes, currentNetwork);
      }
    } catch (e) {
      alert(`Benchmark execution failed: ${e.message}`);
    } finally {
      btn.disabled = false;
      btn.innerHTML = '&#9878; Full Benchmark Arena';
    }
  });

  // Helper to log event messages to the Dynamic Stream
  function appendEventLog(msg, color = '#06b6d4') {
    const logBox = document.getElementById('eventLogs');
    if (!logBox) return;
    if (logBox.innerHTML.includes('No dynamic incidents active')) {
      logBox.innerHTML = '';
    }
    const timeStr = new Date().toLocaleTimeString();
    const entry = document.createElement('div');
    entry.style.cssText = `font-size:0.75rem; color:${color}; margin-bottom:4px; font-family:monospace; line-height:1.3;`;
    entry.innerHTML = `<span style="color:#94a3b8; font-size:0.7rem;">[${timeStr}]</span> ${msg}`;
    logBox.prepend(entry);
  }

  // Update active roadblocks counter badges and modal list
  function updateRoadblockBadges() {
    const incidents = (currentNetwork && currentNetwork.incidents) || [];
    const count = incidents.length;
    const btnBadge = document.getElementById('btnActiveBlockCount');
    if (btnBadge) btnBadge.innerText = count;
    const modalBadge1 = document.getElementById('modalActiveBlockCount');
    if (modalBadge1) modalBadge1.innerText = count;

    renderActiveBlocksList();
  }

  // Populate Active Roadblocks list in modal with individual Clear buttons
  function renderActiveBlocksList() {
    const container = document.getElementById('activeBlocksListContainer');
    if (!container) return;

    const incidents = (currentNetwork && currentNetwork.incidents) || [];
    if (incidents.length === 0) {
      container.innerHTML = `
        <div style="text-align:center; padding:1.5rem; color:#64748b; font-size:0.8rem; background:rgba(0,0,0,0.2); border-radius:6px;">
          No active roadblocks on the network. All road corridors operating smoothly.
        </div>
      `;
      return;
    }

    const nodeMap = {};
    if (currentNetwork && currentNetwork.nodes) {
      currentNetwork.nodes.forEach(n => { nodeMap[n.id] = n; });
    }

    container.innerHTML = incidents.map(inc => {
      const uName = nodeMap[inc.edge_u]?.name || `Node ${inc.edge_u}`;
      const vName = nodeMap[inc.edge_v]?.name || `Node ${inc.edge_v}`;
      const delayMin = Math.round((inc.delay_seconds || 900) / 60);
      const incKey = inc.id || inc.incident_id || `${inc.edge_u}_${inc.edge_v}`;

      return `
        <div style="display:flex; justify-content:space-between; align-items:center; background:rgba(239,68,68,0.12); border:1px solid rgba(239,68,68,0.3); padding:0.6rem 0.8rem; border-radius:6px;">
          <div>
            <div style="font-weight:700; color:#ef4444; font-size:0.82rem;">
              &#9888; ${uName} &harr; ${vName}
            </div>
            <div style="font-size:0.72rem; color:#94a3b8; margin-top:2px;">
              Added Delay: +${delayMin} min | Severity: ${Math.round((inc.severity || 0.95)*100)}% | <em>${inc.description || 'Congestion'}</em>
            </div>
          </div>
          <button onclick="window.removeSingleIncident('${incKey}')" style="padding:0.35rem 0.7rem; font-size:0.75rem; white-space:nowrap; background:#dc2626; color:#fff; border:none; border-radius:4px; font-weight:bold; cursor:pointer;">
            &#10005; Clear Block
          </button>
        </div>
      `;
    }).join('');
  }

  // Populate Corridor Dropdown in Incident Modal with readable corridor names
  function populateCorridorDropdown(selectedU = null, selectedV = null) {
    const select = document.getElementById('incidentCorridorSelect');
    if (!select || !currentNetwork || !currentNetwork.nodes) return;

    const nodeMap = {};
    currentNetwork.nodes.forEach(n => { nodeMap[n.id] = n; });

    let optionsHtml = '';

    // If there's an active solution, prioritize route legs
    if (currentSolution && currentSolution.routes && currentSolution.routes.length > 0) {
      optionsHtml += `<optgroup label="Corridors on Active Fleet Routes">`;
      currentSolution.routes.forEach(route => {
        if (route.detailed_node_path && route.detailed_node_path.length >= 2) {
          const path = route.detailed_node_path;
          for (let i = 0; i < path.length - 1; i++) {
            const u = path[i];
            const v = path[i + 1];
            const uName = nodeMap[u]?.name || `Node ${u}`;
            const vName = nodeMap[v]?.name || `Node ${v}`;
            const isSel = (selectedU !== null && ((u === selectedU && v === selectedV) || (u === selectedV && v === selectedU)));
            optionsHtml += `<option value="${u}_${v}" ${isSel ? 'selected' : ''}>[Route #${route.vehicle_id}] ${uName} ↔ ${vName}</option>`;
          }
        }
      });
      optionsHtml += `</optgroup>`;
    }

    // All network road links
    if (currentNetwork.edges && currentNetwork.edges.length > 0) {
      optionsHtml += `<optgroup label="All Road Network Corridors">`;
      currentNetwork.edges.forEach(e => {
        const uName = nodeMap[e.u]?.name || `Node ${e.u}`;
        const vName = nodeMap[e.v]?.name || `Node ${e.v}`;
        const isSel = (selectedU !== null && ((e.u === selectedU && e.v === selectedV) || (e.u === selectedV && e.v === selectedU)));
        optionsHtml += `<option value="${e.u}_${e.v}" ${isSel ? 'selected' : ''}>${uName} ↔ ${vName} (${e.distance_km} km)</option>`;
      });
      optionsHtml += `</optgroup>`;
    }

    select.innerHTML = optionsHtml;

    // Pre-select first option if none selected
    if (selectedU !== null && selectedV !== null) {
      setCorridorInputFields(selectedU, selectedV);
    } else if (select.value) {
      const parts = select.value.split('_');
      setCorridorInputFields(parseInt(parts[0]), parseInt(parts[1]));
    }
  }

  function setCorridorInputFields(u, v) {
    const inputU = document.getElementById('incidentNodeU');
    const inputV = document.getElementById('incidentNodeV');
    const preview = document.getElementById('corridorPreviewText');

    if (inputU) inputU.value = u;
    if (inputV) inputV.value = v;

    const nodeMap = {};
    if (currentNetwork && currentNetwork.nodes) {
      currentNetwork.nodes.forEach(n => { nodeMap[n.id] = n; });
    }
    const uName = nodeMap[u]?.name || `Node ${u}`;
    const vName = nodeMap[v]?.name || `Node ${v}`;
    if (preview) {
      preview.innerHTML = `Selected Corridor: <strong>${uName} (Node ${u})</strong> &harr; <strong>${vName} (Node ${v})</strong>`;
    }
  }

  function switchIncidentTab(tabName) {
    const panelInject = document.getElementById('panelInjectBlock');
    const panelActive = document.getElementById('panelActiveBlocks');
    const tabInject = document.getElementById('tabBtnInjectBlock');
    const tabActive = document.getElementById('tabBtnActiveBlocks');

    if (tabName === 'inject') {
      if (panelInject) panelInject.style.display = 'block';
      if (panelActive) panelActive.style.display = 'none';
      if (tabInject) tabInject.className = 'btn-primary';
      if (tabActive) tabActive.className = 'btn-slate';
    } else {
      if (panelInject) panelInject.style.display = 'none';
      if (panelActive) panelActive.style.display = 'block';
      if (tabInject) tabInject.className = 'btn-slate';
      if (tabActive) tabActive.className = 'btn-primary';
      renderActiveBlocksList();
    }
  }

  // Global helper for opening incident modal from map edge click
  window.openIncidentModalForEdge = function(u, v) {
    const modal = document.getElementById('incidentModal');
    if (!modal) return;
    populateCorridorDropdown(u, v);
    setCorridorInputFields(u, v);
    switchIncidentTab('inject');
    modal.classList.add('active');
  };

  // Global helper for clearing a specific incident (not all)
  window.removeSingleIncident = async function(incidentId) {
    try {
      const res = await API.removeIncident(incidentId);
      if (currentNetwork) {
        currentNetwork.incidents = res.incidents || [];
        mapView.renderIncidents(currentNetwork.incidents, currentNetwork);
      }
      updateRoadblockBadges();
      appendEventLog(`✅ <strong style="color:#10b981;">ROADBLOCK REMOVED</strong>: Cleared specific roadblock corridor. Free-flow traffic restored.`, '#10b981');
    } catch (e) {
      alert(`Failed to remove roadblock: ${e.message}`);
    }
  };

  // 4. Incident Injection Button & Modal Handlers
  const incidentModal = document.getElementById('incidentModal');

  document.getElementById('btnAddIncident').addEventListener('click', () => {
    if (!currentNetwork || !currentNetwork.nodes || currentNetwork.nodes.length < 2) {
      alert('Please wait for a city network to load first.');
      return;
    }
    populateCorridorDropdown();
    switchIncidentTab('inject');
    incidentModal.classList.add('active');
  });

  document.getElementById('btnCloseIncidentModal')?.addEventListener('click', () => {
    incidentModal.classList.remove('active');
  });

  document.getElementById('btnCancelIncidentModal')?.addEventListener('click', () => {
    incidentModal.classList.remove('active');
  });

  document.getElementById('btnCloseActiveBlocksModal')?.addEventListener('click', () => {
    incidentModal.classList.remove('active');
  });

  document.getElementById('tabBtnInjectBlock')?.addEventListener('click', () => {
    switchIncidentTab('inject');
  });

  document.getElementById('tabBtnActiveBlocks')?.addEventListener('click', () => {
    switchIncidentTab('active');
  });

  document.getElementById('incidentCorridorSelect')?.addEventListener('change', (e) => {
    const val = e.target.value;
    if (val && val.includes('_')) {
      const [u, v] = val.split('_').map(Number);
      setCorridorInputFields(u, v);
    }
  });

  document.getElementById('incidentNodeU')?.addEventListener('input', () => {
    const u = parseInt(document.getElementById('incidentNodeU').value);
    const v = parseInt(document.getElementById('incidentNodeV').value);
    if (!isNaN(u) && !isNaN(v)) setCorridorInputFields(u, v);
  });

  document.getElementById('incidentNodeV')?.addEventListener('input', () => {
    const u = parseInt(document.getElementById('incidentNodeU').value);
    const v = parseInt(document.getElementById('incidentNodeV').value);
    if (!isNaN(u) && !isNaN(v)) setCorridorInputFields(u, v);
  });

  // Confirm injection of specific blocked portion
  document.getElementById('btnConfirmInjectIncident')?.addEventListener('click', async () => {
    const u = parseInt(document.getElementById('incidentNodeU').value);
    const v = parseInt(document.getElementById('incidentNodeV').value);
    const delay = parseFloat(document.getElementById('incidentDelaySelect').value) || 900.0;
    const severity = parseFloat(document.getElementById('incidentSeveritySelect').value) || 0.95;
    const desc = document.getElementById('incidentDescription').value || 'Traffic Roadblock';

    if (isNaN(u) || isNaN(v)) {
      alert('Please enter or select valid Start and End node IDs for the roadblock.');
      return;
    }

    const nodeMap = {};
    if (currentNetwork && currentNetwork.nodes) {
      currentNetwork.nodes.forEach(n => { nodeMap[n.id] = n; });
    }
    const uName = nodeMap[u]?.name || `Node ${u}`;
    const vName = nodeMap[v]?.name || `Node ${v}`;

    try {
      const res = await API.addIncident({
        edge_u: u,
        edge_v: v,
        severity: severity,
        delay_seconds: delay,
        duration_seconds: 3600.0,
        description: `${desc}: ${uName} ↔ ${vName}`,
      });

      currentNetwork.incidents = res.incidents || [res.incident];
      mapView.renderIncidents(currentNetwork.incidents, currentNetwork);
      updateRoadblockBadges();
      incidentModal.classList.remove('active');

      const delayMin = Math.round(delay / 60);
      appendEventLog(`⚠️ <strong style="color:#ef4444;">ROADBLOCK INJECTED</strong>: Corridor <strong>${uName}</strong> &harr; <strong>${vName}</strong> (+${delayMin} min delay, ${(severity*100).toFixed(0)}% blockage).`, '#ef4444');
      appendEventLog(`⚡ <strong style="color:#06b6d4;">QUANTUM OBSERVER</strong>: Live rerouting algorithm engaged. Monitoring fleet trajectory...`, '#06b6d4');

      if (res.reroute_events && res.reroute_events.length > 0) {
        res.reroute_events.forEach(evt => {
          appendEventLog(`⚡ [Vehicle ${evt.vehicle_id}] ${evt.message}`, '#10b981');
        });
      }
    } catch (e) {
      alert(`Failed to add roadblock: ${e.message}`);
    }
  });

  // Clear Roadblock Toolbar Button
  document.getElementById('btnClearIncidents').addEventListener('click', async () => {
    const incidents = (currentNetwork && currentNetwork.incidents) || [];
    if (incidents.length === 0) {
      alert('No active roadblocks are currently on the road network.');
      return;
    }

    if (incidents.length === 1) {
      const inc = incidents[0];
      const incKey = inc.id || inc.incident_id || `${inc.edge_u}_${inc.edge_v}`;
      await window.removeSingleIncident(incKey);
      return;
    }

    // Multiple roadblocks: open the Active Blocks manager so user chooses which specific block to clear
    populateCorridorDropdown();
    switchIncidentTab('active');
    incidentModal.classList.add('active');
  });

  // Clear All Blocks Modal Button
  document.getElementById('btnClearAllBlocksModal')?.addEventListener('click', async () => {
    if (!confirm('Are you sure you want to clear ALL active roadblocks on the network?')) return;
    try {
      await API.clearIncidents();
      if (currentNetwork) {
        currentNetwork.incidents = [];
        mapView.renderIncidents([], currentNetwork);
      }
      updateRoadblockBadges();
      incidentModal.classList.remove('active');
      appendEventLog(`✅ All dynamic roadblocks cleared. Traffic restored to free-flow velocity.`, '#10b981');
    } catch (e) {
      console.error('Failed to clear incidents:', e);
    }
  });

  // 5. Traffic Simulation Controls
  document.getElementById('btnSimPlay').addEventListener('click', async () => {
    if (isSimulating) {
      // Pause
      clearInterval(simTimer);
      isSimulating = false;
      document.getElementById('btnSimPlay').innerHTML = '&#9658; Play Sim';
      return;
    }

    if (!currentSolution) {
      alert('Please run Optimization first before simulating traffic fleet movement.');
      return;
    }

    try {
      await API.startSimulation();
      isSimulating = true;
      document.getElementById('btnSimPlay').innerHTML = '&#10074;&#10074; Pause';

      simTimer = setInterval(async () => {
        const state = await API.stepSimulation();
        mapView.updateVehicleAgents(state.agents);

        // Update live time
        document.getElementById('simClock').innerText = state.sim_time_formatted;

        // Render Reroute Event log
        if (state.reroute_events && state.reroute_events.length > 0) {
          const logBox = document.getElementById('eventLogs');
          if (logBox) {
            logBox.innerHTML = state.reroute_events
              .map(e => `<div style="font-size:0.75rem; color:#10b981; margin-bottom:4px; font-family:monospace; line-height:1.3;">[⚡ Vehicle ${e.vehicle_id || 'Fleet'}] ${e.message}</div>`)
              .join('');
          }
        }

        if (state.all_completed) {
          clearInterval(simTimer);
          isSimulating = false;
          document.getElementById('btnSimPlay').innerHTML = '&#9658; Play Sim';
          alert('All delivery vehicles have completed their dynamic routes and returned to depot.');
        }
      }, 500);
    } catch (e) {
      alert(`Simulation error: ${e.message}`);
      isSimulating = false;
      document.getElementById('btnSimPlay').innerHTML = '&#9658; Play Sim';
    }
  });

  // Export Buttons
  document.getElementById('btnExportJson').addEventListener('click', () => {
    window.open(API.getExportUrl('json'), '_blank');
  });

  document.getElementById('btnExportCsv').addEventListener('click', () => {
    window.open(API.getExportUrl('csv'), '_blank');
  });

  // Delivery Table Modal Handlers
  const modal = document.getElementById('deliverablesModal');
  document.getElementById('btnViewDeliverables').addEventListener('click', () => {
    modal.classList.add('active');
  });
  document.getElementById('btnCloseModal').addEventListener('click', () => {
    modal.classList.remove('active');
  });
});
