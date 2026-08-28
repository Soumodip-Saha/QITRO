/**
 * Advanced Analytics, Statistical Hypothesis Testing, Scalability,
 * and Quantum Mechanics Visualizer Module for QITRO
 */

class AdvancedAnalyticsView {
  constructor() {
    this.convergenceChart = null;
    this.scalabilityChart = null;
    this.entropyChart = null;
    this.paretoChart = null;

    this.initTabs();
    this.initCharts();
    this.bindEvents();
    this.loadQuantumTheoryContent();
  }

  initTabs() {
    const tabBtns = document.querySelectorAll('.nav-tab-btn');
    tabBtns.forEach(btn => {
      btn.addEventListener('click', () => {
        const targetTab = btn.getAttribute('data-tab');

        tabBtns.forEach(b => b.classList.remove('active'));
        btn.classList.add('active');

        document.querySelectorAll('.tab-content-panel').forEach(panel => {
          panel.classList.remove('active');
        });

        const activePanel = document.getElementById(targetTab);
        if (activePanel) activePanel.classList.add('active');

        // Trigger chart resize on tab switch
        if (targetTab === 'tabConvergence' && this.convergenceChart) this.convergenceChart.resize();
        if (targetTab === 'tabScalability' && this.scalabilityChart) this.scalabilityChart.resize();
      });
    });
  }

  initCharts() {
    // 1. Solution Convergence Profile Chart
    const convCanvas = document.getElementById('advancedConvergenceChart');
    if (convCanvas) {
      this.convergenceChart = new Chart(convCanvas, {
        type: 'line',
        data: { labels: [], datasets: [] },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          interaction: { mode: 'index', intersect: false },
          scales: {
            x: { title: { display: true, text: 'Iteration / Generation t', color: '#94a3b8' }, grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#94a3b8' } },
            y: { title: { display: true, text: 'Multi-Objective Cost Fitness', color: '#94a3b8' }, grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#94a3b8' } },
          },
          plugins: { legend: { labels: { color: '#f8fafc', boxWidth: 12 } } },
        },
      });
    }

    // 2. Quantum Entropy & Alpha Dynamics Chart
    const entropyCanvas = document.getElementById('quantumEntropyChart');
    if (entropyCanvas) {
      this.entropyChart = new Chart(entropyCanvas, {
        type: 'line',
        data: { labels: [], datasets: [] },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          scales: {
            x: { title: { display: true, text: 'Iteration t', color: '#94a3b8' }, grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#94a3b8' } },
            y: { title: { display: true, text: 'Quantum Entropy S(t) / α(t)', color: '#94a3b8' }, grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#94a3b8' } },
          },
          plugins: { legend: { labels: { color: '#f8fafc', boxWidth: 12 } } },
        },
      });
    }

    // 3. Scalability Profiling Curve Chart
    const scaleCanvas = document.getElementById('scalabilityChart');
    if (scaleCanvas) {
      this.scalabilityChart = new Chart(scaleCanvas, {
        type: 'line',
        data: { labels: [], datasets: [] },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          scales: {
            x: { title: { display: true, text: 'Problem Scale N (Customers)', color: '#94a3b8' }, grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#94a3b8' } },
            y: { title: { display: true, text: 'Execution Runtime (ms)', color: '#94a3b8' }, grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#94a3b8' } },
          },
          plugins: { legend: { labels: { color: '#f8fafc', boxWidth: 12 } } },
        },
      });
    }
  }

  bindEvents() {
    // Run Convergence Profile
    const btnRunConv = document.getElementById('btnRunConvergenceProfile');
    if (btnRunConv) {
      btnRunConv.addEventListener('click', async () => {
        btnRunConv.disabled = true;
        btnRunConv.innerText = 'Profiling Convergence...';
        try {
          const algo = document.getElementById('convAlgoSelect').value;
          const runs = parseInt(document.getElementById('convRunsInput').value) || 5;
          const iters = parseInt(document.getElementById('convItersInput').value) || 80;

          const data = await API.getConvergenceProfile({
            algorithm: algo,
            num_runs: runs,
            max_iterations: iters,
          });

          this.renderConvergenceProfile(data);
        } catch (e) {
          alert('Convergence profiling failed: ' + e.message);
        } finally {
          btnRunConv.disabled = false;
          btnRunConv.innerHTML = '&#9889; Run Convergence Profile';
        }
      });
    }

    // Run Hypothesis Testing
    const btnRunHypo = document.getElementById('btnRunHypothesisTesting');
    if (btnRunHypo) {
      btnRunHypo.addEventListener('click', async () => {
        btnRunHypo.disabled = true;
        btnRunHypo.innerText = 'Testing Hypotheses...';
        try {
          const qAlgo = document.getElementById('hypoQuantumAlgo').value;
          const cAlgo = document.getElementById('hypoClassicalAlgo').value;
          const runs = parseInt(document.getElementById('hypoRunsInput').value) || 8;

          const res = await API.runHypothesisTesting({
            quantum_algo: qAlgo,
            classical_algo: cAlgo,
            num_runs: runs,
            iterations: 80,
          });

          this.renderHypothesisResults(res);
        } catch (e) {
          alert('Hypothesis testing failed: ' + e.message);
        } finally {
          btnRunHypo.disabled = false;
          btnRunHypo.innerHTML = '&#9878; Run Hypothesis Tests';
        }
      });
    }

    // Run Scalability Profiler
    const btnRunScale = document.getElementById('btnRunScalability');
    if (btnRunScale) {
      btnRunScale.addEventListener('click', async () => {
        btnRunScale.disabled = true;
        btnRunScale.innerText = 'Profiling Scalability N=10..250...';
        try {
          const data = await API.getScalabilityProfile({
            node_sizes: [10, 25, 50, 100, 250],
          });
          this.renderScalabilityProfile(data);
        } catch (e) {
          alert('Scalability profiling failed: ' + e.message);
        } finally {
          btnRunScale.disabled = false;
          btnRunScale.innerHTML = '&#128200; Run Scalability Suite (N=10..250)';
        }
      });
    }
  }

  renderConvergenceProfile(data) {
    if (!this.convergenceChart || !this.entropyChart) return;

    // Update Convergence Chart with Mean and 1-Sigma Band
    this.convergenceChart.data.labels = data.iterations;
    this.convergenceChart.data.datasets = [
      {
        label: `${data.algorithm} Mean Fitness`,
        data: data.mean_fitness,
        borderColor: '#06b6d4',
        backgroundColor: 'rgba(6, 182, 212, 0.15)',
        borderWidth: 2.5,
        fill: false,
        pointRadius: 0,
      },
      {
        label: `+1σ Upper Bound`,
        data: data.upper_band_1sigma,
        borderColor: 'rgba(6, 182, 212, 0.3)',
        borderDash: [4, 4],
        borderWidth: 1,
        fill: false,
        pointRadius: 0,
      },
      {
        label: `-1σ Lower Bound`,
        data: data.lower_band_1sigma,
        borderColor: 'rgba(6, 182, 212, 0.3)',
        borderDash: [4, 4],
        borderWidth: 1,
        fill: '-1',
        backgroundColor: 'rgba(6, 182, 212, 0.08)',
        pointRadius: 0,
      },
    ];
    this.convergenceChart.update();

    // Update Quantum Entropy & Alpha Decay Chart
    this.entropyChart.data.labels = data.iterations;
    this.entropyChart.data.datasets = [
      {
        label: 'Quantum Contraction Parameter α(t)',
        data: data.alpha_trajectory,
        borderColor: '#f59e0b',
        borderWidth: 2,
        fill: false,
        pointRadius: 0,
      },
      {
        label: 'Quantum Phase-Space Entropy S(t)',
        data: data.quantum_entropy,
        borderColor: '#a855f7',
        borderWidth: 2,
        fill: false,
        pointRadius: 0,
      },
    ];
    this.entropyChart.update();

    // Update Summary Stats Box
    const sumBox = document.getElementById('convSummaryBox');
    if (sumBox && data.summary) {
      sumBox.innerHTML = `
        <div class="metric-card" style="border-left-color:#06b6d4;">
          <div class="metric-label">Initial Cost</div>
          <div class="metric-val">${data.summary.initial_cost}</div>
        </div>
        <div class="metric-card" style="border-left-color:#10b981;">
          <div class="metric-label">Optimized Cost</div>
          <div class="metric-val">${data.summary.final_cost}</div>
        </div>
        <div class="metric-card" style="border-left-color:#a855f7;">
          <div class="metric-label">Improvement</div>
          <div class="metric-val">${data.summary.total_improvement_pct}%</div>
        </div>
        <div class="metric-card" style="border-left-color:#f59e0b;">
          <div class="metric-label">95% Conv. Iteration</div>
          <div class="metric-val">${data.summary.iterations_to_95pct_optimum}</div>
        </div>
      `;
    }
  }

  renderHypothesisResults(res) {
    const card = document.getElementById('hypothesisResultCard');
    if (!card) return;

    card.innerHTML = `
      <div style="background:rgba(15,23,42,0.9); border:1px solid var(--border-color); border-radius:8px; padding:1rem; margin-top:0.75rem;">
        <h4 style="color:var(--quantum-cyan); font-size:0.95rem; margin-bottom:0.6rem;">
          Statistical Significance Matrix: ${res.quantum_algorithm} vs ${res.classical_algorithm} (N=${res.num_trials} Trials)
        </h4>
        
        <div style="display:grid; grid-template-columns:repeat(4, 1fr); gap:0.5rem; margin-bottom:0.8rem;">
          <div class="metric-card">
            <div class="metric-label">Quantum Mean</div>
            <div class="metric-val" style="color:#06b6d4;">${res.quantum_mean}</div>
          </div>
          <div class="metric-card">
            <div class="metric-label">Classical Mean</div>
            <div class="metric-val" style="color:#94a3b8;">${res.classical_mean}</div>
          </div>
          <div class="metric-card">
            <div class="metric-label">Mean Difference</div>
            <div class="metric-val" style="color:#10b981;">+${res.mean_difference} (${res.percentage_improvement}%)</div>
          </div>
          <div class="metric-card">
            <div class="metric-label">Cohen's d Effect Size</div>
            <div class="metric-val" style="color:#a855f7;">${res.cohens_d} <span style="font-size:0.7rem;">(${res.effect_magnitude})</span></div>
          </div>
        </div>

        <table class="benchmark-table" style="font-size:0.8rem;">
          <thead>
            <tr>
              <th>Statistical Test</th>
              <th>Test Type</th>
              <th>Test Statistic</th>
              <th>p-Value</th>
              <th>Significance (α = 0.05)</th>
              <th>Conclusion</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td><strong>Wilcoxon Signed-Rank Test</strong></td>
              <td>Non-parametric paired ranks</td>
              <td>W = ${res.wilcoxon.statistic}</td>
              <td style="color:${res.wilcoxon.is_significant ? '#10b981' : '#f59e0b'}; font-weight:700;">p = ${res.wilcoxon.p_value}</td>
              <td>${res.wilcoxon.is_significant ? '<span style="color:#10b981;">✔ Reject Null (H₀)</span>' : '<span style="color:#94a3b8;">Fail to Reject</span>'}</td>
              <td>${res.wilcoxon.interpretation}</td>
            </tr>
            <tr>
              <td><strong>Paired Student's t-Test</strong></td>
              <td>Parametric paired means</td>
              <td>t = ${res.paired_ttest.t_statistic}</td>
              <td style="color:${res.paired_ttest.is_significant ? '#10b981' : '#f59e0b'}; font-weight:700;">p = ${res.paired_ttest.p_value}</td>
              <td>${res.paired_ttest.is_significant ? '<span style="color:#10b981;">✔ Reject Null (H₀)</span>' : '<span style="color:#94a3b8;">Fail to Reject</span>'}</td>
              <td>Statistically significant mean difference at 95% CI</td>
            </tr>
            <tr>
              <td><strong>Mann-Whitney U Test</strong></td>
              <td>Non-parametric independent ranks</td>
              <td>U = ${res.mann_whitney_u.u_statistic}</td>
              <td style="color:${res.mann_whitney_u.is_significant ? '#10b981' : '#f59e0b'}; font-weight:700;">p = ${res.mann_whitney_u.p_value}</td>
              <td>${res.mann_whitney_u.is_significant ? '<span style="color:#10b981;">✔ Significant</span>' : '<span style="color:#94a3b8;">Not Significant</span>'}</td>
              <td>Distribution stochastic dominance confirmed</td>
            </tr>
          </tbody>
        </table>
      </div>
    `;
  }

  renderScalabilityProfile(data) {
    if (!this.scalabilityChart || !data.scaling_data) return;

    const labels = data.scaling_data.map(d => `N=${d.num_customers}`);
    const qpsoTimes = data.scaling_data.map(d => d.qpso_runtime_ms);
    const psoTimes = data.scaling_data.map(d => d.pso_runtime_ms);
    const gaTimes = data.scaling_data.map(d => d.ga_runtime_ms);

    this.scalabilityChart.data.labels = labels;
    this.scalabilityChart.data.datasets = [
      {
        label: 'QPSO Runtime (ms)',
        data: qpsoTimes,
        borderColor: '#06b6d4',
        backgroundColor: 'rgba(6, 182, 212, 0.2)',
        borderWidth: 2.5,
        fill: false,
      },
      {
        label: 'Classical PSO Runtime (ms)',
        data: psoTimes,
        borderColor: '#3b82f6',
        borderWidth: 2,
        fill: false,
      },
      {
        label: 'Classical GA Runtime (ms)',
        data: gaTimes,
        borderColor: '#10b981',
        borderWidth: 2,
        fill: false,
      },
    ];
    this.scalabilityChart.update();

    // Render Scalability Table
    const tableBody = document.getElementById('scalabilityTableBody');
    if (tableBody) {
      tableBody.innerHTML = data.scaling_data.map(d => `
        <tr>
          <td><strong>N = ${d.num_customers}</strong></td>
          <td><code>${d.search_space_size}</code></td>
          <td style="color:#06b6d4; font-weight:700;">${d.qpso_runtime_ms} ms</td>
          <td>${d.pso_runtime_ms} ms</td>
          <td>${d.ga_runtime_ms} ms</td>
          <td style="color:#10b981; font-weight:700;">${d.qpso_fitness}</td>
          <td>${d.pso_fitness}</td>
          <td><span style="color:#10b981; font-weight:700;">+${d.qpso_advantage_pct}%</span></td>
        </tr>
      `).join('');
    }
  }

  async loadQuantumTheoryContent() {
    try {
      const theory = await API.getQuantumMathTheory();
      const container = document.getElementById('quantumTheoryContent');
      if (!container || !theory) return;

      container.innerHTML = `
        <div style="display:grid; grid-template-columns:1fr 1fr; gap:1rem;">
          <div class="glass-panel" style="padding:1rem; border-left:3px solid #06b6d4;">
            <h3 style="color:#06b6d4; font-size:0.95rem; margin-bottom:0.5rem;">${theory.quantum_potential_well.title}</h3>
            <p style="font-size:0.8rem; color:#94a3b8; margin-bottom:0.5rem;">Schrödinger Equation in 1D δ-Potential Well:</p>
            <div style="background:rgba(0,0,0,0.4); padding:0.5rem; border-radius:4px; font-family:monospace; font-size:0.85rem; color:#f8fafc; margin-bottom:0.5rem;">
              [- (ℏ²/2m) d²ψ/dx² - γ δ(x - p)] ψ(x) = E ψ(x)
            </div>
            <p style="font-size:0.8rem; color:#94a3b8; margin-bottom:0.5rem;">Normalized Wave Function & Probability Density:</p>
            <div style="background:rgba(0,0,0,0.4); padding:0.5rem; border-radius:4px; font-family:monospace; font-size:0.82rem; color:#22d3ee; margin-bottom:0.5rem;">
              ψ(x) = (1/√L) exp(-|x - p| / L)<br>
              Q(x) = |ψ(x)|² = (1/L) exp(-2|x - p| / L)
            </div>
            <p style="font-size:0.8rem; color:#94a3b8; margin-bottom:0.5rem;">Monte Carlo State Sampling Equation:</p>
            <div style="background:rgba(0,0,0,0.4); padding:0.5rem; border-radius:4px; font-family:monospace; font-size:0.82rem; color:#10b981;">
              x(t+1) = p ± α |mbest - x| ln(1/u),  u ~ U(0,1)
            </div>
          </div>

          <div class="glass-panel" style="padding:1rem; border-left:3px solid #a855f7;">
            <h3 style="color:#a855f7; font-size:0.95rem; margin-bottom:0.5rem;">${theory.quantum_genetic_mechanics.title}</h3>
            <p style="font-size:0.8rem; color:#94a3b8; margin-bottom:0.5rem;">Q-Bit State Vector & Superposition:</p>
            <div style="background:rgba(0,0,0,0.4); padding:0.5rem; border-radius:4px; font-family:monospace; font-size:0.82rem; color:#f8fafc; margin-bottom:0.5rem;">
              |q⟩ = [α, β]ᵀ = cos(θ)|0⟩ + sin(θ)|1⟩, where |α|² + |β|² = 1
            </div>
            <p style="font-size:0.8rem; color:#94a3b8; margin-bottom:0.5rem;">Quantum Rotation Gate Unitary Transformation U(Δθ):</p>
            <div style="background:rgba(0,0,0,0.4); padding:0.5rem; border-radius:4px; font-family:monospace; font-size:0.82rem; color:#e879f9; margin-bottom:0.5rem;">
              [α(t+1), β(t+1)]ᵀ = [cos(Δθ) -sin(Δθ); sin(Δθ) cos(Δθ)] [α(t), β(t)]ᵀ
            </div>
            <p style="font-size:0.8rem; color:#94a3b8; margin-bottom:0.5rem;">Pauli-X Quantum NOT Gate Mutation:</p>
            <div style="background:rgba(0,0,0,0.4); padding:0.5rem; border-radius:4px; font-family:monospace; font-size:0.82rem; color:#f59e0b;">
              σ_x = [0 1; 1 0] ⇒ σ_x [α, β]ᵀ = [β, α]ᵀ
            </div>
          </div>

          <div class="glass-panel" style="padding:1rem; border-left:3px solid #f59e0b;">
            <h3 style="color:#f59e0b; font-size:0.95rem; margin-bottom:0.5rem;">${theory.quantum_annealing_tunneling.title}</h3>
            <p style="font-size:0.8rem; color:#94a3b8; margin-bottom:0.5rem;">Transverse-Field Ising Hamiltonian:</p>
            <div style="background:rgba(0,0,0,0.4); padding:0.5rem; border-radius:4px; font-family:monospace; font-size:0.82rem; color:#f8fafc; margin-bottom:0.5rem;">
              H(t) = H_cost(R) - Γ(t) ∑ σ_i^x
            </div>
            <p style="font-size:0.8rem; color:#94a3b8; margin-bottom:0.5rem;">Quantum Tunneling Acceptance Probability:</p>
            <div style="background:rgba(0,0,0,0.4); padding:0.5rem; border-radius:4px; font-family:monospace; font-size:0.82rem; color:#fcd34d;">
              P_accept = min(1, exp(-ΔE / k_B T) + tanh(Γ(t) / (T(t) + ε)))
            </div>
          </div>

          <div class="glass-panel" style="padding:1rem; border-left:3px solid #10b981;">
            <h3 style="color:#10b981; font-size:0.95rem; margin-bottom:0.5rem;">Dynamic Traffic Congestion & Emission Models</h3>
            <p style="font-size:0.8rem; color:#94a3b8; margin-bottom:0.5rem;">BPR Dynamic Link Performance Function:</p>
            <div style="background:rgba(0,0,0,0.4); padding:0.5rem; border-radius:4px; font-family:monospace; font-size:0.82rem; color:#f8fafc; margin-bottom:0.5rem;">
              T_ij(t) = (d_ij / v_max) [1 + 0.15 (V_ij(t) / C_ij)⁴] + δ_incident(t)
            </div>
            <p style="font-size:0.8rem; color:#94a3b8; margin-bottom:0.5rem;">CMEM Carbon Footprint Model:</p>
            <div style="background:rgba(0,0,0,0.4); padding:0.5rem; border-radius:4px; font-family:monospace; font-size:0.82rem; color:#6ee7b7;">
              CO2(g) = d_ij · (k₀ + k₁ v̄ + k₂ v̄²) · (1 + 0.05 · gradient%)
            </div>
          </div>
        </div>
      `;
    } catch (e) {
      console.error('Failed to load quantum theory metadata:', e);
    }
  }
}

// Instantiate on load
document.addEventListener('DOMContentLoaded', () => {
  window.advancedAnalyticsView = new AdvancedAnalyticsView();
});
