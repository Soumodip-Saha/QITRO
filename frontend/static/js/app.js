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

  // 4. Incident Injection Handler
  document.getElementById('btnAddIncident').addEventListener('click', async () => {
    if (!currentNetwork || !currentNetwork.nodes || currentNetwork.nodes.length < 2) {
      alert('Please select or wait for a city network to load first.');
      return;
    }

    // Auto-select target edge:
    // 1. If an optimized route exists, pick an edge on Vehicle 1's planned path (or another vehicle's)
    let targetU = null;
    let targetV = null;

    if (currentSolution && currentSolution.routes && currentSolution.routes.length > 0) {
      for (const route of currentSolution.routes) {
        if (route.detailed_node_path && route.detailed_node_path.length >= 2) {
          const path = route.detailed_node_path;
          for (let i = 0; i < path.length - 1; i++) {
            const u = path[i];
            const v = path[i + 1];
            const alreadyHasInc = currentNetwork.incidents && currentNetwork.incidents.some(
              inc => (inc.edge_u === u && inc.edge_v === v) || (inc.edge_u === v && inc.edge_v === u)
            );
            if (!alreadyHasInc) {
              targetU = u;
              targetV = v;
              break;
            }
          }
          if (targetU !== null) break;
        }
      }
    }

    // Fallback: pick an edge from network
    if (targetU === null && currentNetwork.edges && currentNetwork.edges.length > 0) {
      for (const edge of currentNetwork.edges) {
        const alreadyHasInc = currentNetwork.incidents && currentNetwork.incidents.some(
          inc => (inc.edge_u === edge.u && inc.edge_v === edge.v) || (inc.edge_u === edge.v && inc.edge_v === edge.u)
        );
        if (!alreadyHasInc) {
          targetU = edge.u;
          targetV = edge.v;
          break;
        }
      }
    }

    if (targetU === null) {
      targetU = currentNetwork.nodes[0].id;
      targetV = currentNetwork.nodes[1].id;
    }

    const nodeMap = {};
    currentNetwork.nodes.forEach(n => { nodeMap[n.id] = n; });
    const uName = nodeMap[targetU]?.name || `Node ${targetU}`;
    const vName = nodeMap[targetV]?.name || `Node ${targetV}`;

    try {
      const res = await API.addIncident({
        edge_u: targetU,
        edge_v: targetV,
        severity: 0.95,
        delay_seconds: 900.0,
        duration_seconds: 3600.0,
        description: `Severe Congestion & Roadblock: ${uName} ↔ ${vName}`,
      });

      // Update current network's incidents directly
      currentNetwork.incidents = res.incidents || [res.incident];
      mapView.renderIncidents(currentNetwork.incidents, currentNetwork);

      // Immediately log to event stream
      appendEventLog(`⚠️ <strong style="color:#ef4444;">ROADBLOCK INJECTED</strong>: Congestion on <strong>${uName}</strong> &harr; <strong>${vName}</strong> (+15 min delay).`, '#ef4444');
      appendEventLog(`⚡ <strong style="color:#06b6d4;">QUANTUM OBSERVER</strong>: Real-time rerouting engaged. Monitoring fleet trajectory...`, '#06b6d4');

      if (res.reroute_events && res.reroute_events.length > 0) {
        res.reroute_events.forEach(evt => {
          appendEventLog(`⚡ [Vehicle ${evt.vehicle_id}] ${evt.message}`, '#10b981');
        });
      }
    } catch (e) {
      alert(`Failed to add incident: ${e.message}`);
    }
  });

  // Clear Incidents Handler
  document.getElementById('btnClearIncidents').addEventListener('click', async () => {
    try {
      await API.clearIncidents();
      if (currentNetwork) {
        currentNetwork.incidents = [];
        mapView.renderIncidents([], currentNetwork);
      }
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
