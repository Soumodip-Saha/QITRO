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

  // 4. Incident Injection Handler
  document.getElementById('btnAddIncident').addEventListener('click', async () => {
    const u = parseInt(prompt('Enter start intersection Node ID for roadblock (e.g. 6):', '6'));
    const v = parseInt(prompt('Enter end intersection Node ID (e.g. 2):', '2'));

    if (isNaN(u) || isNaN(v)) return;

    try {
      const res = await API.addIncident({
        edge_u: u,
        edge_v: v,
        severity: 0.9,
        delay_seconds: 900.0,
        duration_seconds: 3600.0,
        description: `Severe Congestion & Roadblock between [${u}] and [${v}]`,
      });

      alert(`Active Incident Injected: ${res.incident.description}`);
      // Refresh network
      const cityId = document.getElementById('citySelect').value;
      await loadCity(cityId);
      if (currentSolution) {
        mapView.renderRoutes(currentSolution.routes, currentNetwork);
      }
    } catch (e) {
      alert(`Failed to add incident: ${e.message}`);
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
        const logBox = document.getElementById('eventLogs');
        if (logBox && state.reroute_events && state.reroute_events.length > 0) {
          logBox.innerHTML = state.reroute_events
            .map(e => `<div style="font-size:0.75rem; color:#06b6d4; margin-bottom:4px;">[${e.vehicle_id ? 'Vehicle ' + e.vehicle_id : 'System'}] ${e.message}</div>`)
            .join('');
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
