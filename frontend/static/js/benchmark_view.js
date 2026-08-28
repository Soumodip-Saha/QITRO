/**
 * Benchmark Analytics & Live Convergence Chart View
 */

class BenchmarkView {
  constructor(canvasId) {
    this.canvasId = canvasId;
    this.chart = null;
    this.initChart();
  }

  initChart() {
    const ctx = document.getElementById(this.canvasId);
    if (!ctx) return;

    this.chart = new Chart(ctx, {
      type: 'line',
      data: {
        labels: [],
        datasets: [],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        animation: { duration: 300 },
        interaction: { mode: 'index', intersect: false },
        scales: {
          x: {
            title: { display: true, text: 'Iteration / Generation', color: '#94a3b8', font: { size: 10 } },
            grid: { color: 'rgba(255, 255, 255, 0.05)' },
            ticks: { color: '#94a3b8', font: { size: 10 } },
          },
          y: {
            title: { display: true, text: 'Multi-Objective Cost / Fitness', color: '#94a3b8', font: { size: 10 } },
            grid: { color: 'rgba(255, 255, 255, 0.05)' },
            ticks: { color: '#94a3b8', font: { size: 10 } },
          },
        },
        plugins: {
          legend: {
            labels: { color: '#f8fafc', font: { size: 10 }, boxWidth: 12 },
          },
        },
      },
    });
  }

  updateSingleRunConvergence(algorithmName, history) {
    if (!this.chart) return;
    const labels = history.map((_, idx) => idx + 1);

    this.chart.data.labels = labels;
    this.chart.data.datasets = [
      {
        label: algorithmName,
        data: history,
        borderColor: '#06b6d4',
        backgroundColor: 'rgba(6, 182, 212, 0.1)',
        borderWidth: 2,
        fill: true,
        tension: 0.2,
        pointRadius: 0,
      },
    ];
    this.chart.update();
  }

  updateMultiAlgorithmBenchmark(benchmarkData) {
    if (!this.chart || !benchmarkData.convergence_curves) return;

    const colors = {
      QPSO: '#06b6d4',
      QGA: '#a855f7',
      QSA: '#ec4899',
      PSO: '#3b82f6',
      GA: '#10b981',
      SA: '#f59e0b',
      CLARKE_WRIGHT: '#64748b',
    };

    let maxLen = 0;
    const datasets = [];

    for (const [algoKey, curve] of Object.entries(benchmarkData.convergence_curves)) {
      if (curve.length > maxLen) maxLen = curve.length;
      datasets.push({
        label: algoKey,
        data: curve,
        borderColor: colors[algoKey] || '#ffffff',
        borderWidth: algoKey.startsWith('Q') ? 2.5 : 1.5,
        fill: false,
        tension: 0.2,
        pointRadius: 0,
      });
    }

    this.chart.data.labels = Array.from({ length: maxLen }, (_, i) => i + 1);
    this.chart.data.datasets = datasets;
    this.chart.update();

    // Update Comparison Table
    this.renderComparisonTable(benchmarkData);
  }

  renderComparisonTable(benchmarkData) {
    const tableBody = document.getElementById('benchmarkTableBody');
    if (!tableBody || !benchmarkData.summaries) return;

    tableBody.innerHTML = '';

    for (const [key, sum] of Object.entries(benchmarkData.summaries)) {
      const isQuantum = key.startsWith('Q');
      const row = document.createElement('tr');
      if (isQuantum) row.className = 'highlight-quantum';

      row.innerHTML = `
        <td><strong>${sum.algorithm_name}</strong></td>
        <td>${sum.fitness_mean.toFixed(2)} &plusmn; ${sum.fitness_std.toFixed(2)}</td>
        <td>${sum.distance_mean_km.toFixed(1)} km</td>
        <td>${Math.round(sum.travel_time_mean_sec / 60)} min</td>
        <td>${sum.co2_mean_kg.toFixed(2)} kg</td>
        <td>${sum.computation_time_mean_ms.toFixed(1)} ms</td>
        <td><span style="color:${sum.feasibility_rate_pct >= 90 ? '#10b981' : '#f59e0b'};">${sum.feasibility_rate_pct}%</span></td>
      `;
      tableBody.appendChild(row);
    }

    // Render Wilcoxon Badges
    const wilcoxonContainer = document.getElementById('wilcoxonBadges');
    if (wilcoxonContainer && benchmarkData.wilcoxon_significance) {
      wilcoxonContainer.innerHTML = '';
      for (const [testName, res] of Object.entries(benchmarkData.wilcoxon_significance)) {
        const badge = document.createElement('div');
        badge.className = 'metric-card';
        badge.style.borderLeftColor = res.is_significant ? '#10b981' : '#64748b';
        badge.innerHTML = `
          <div class="metric-label">${testName.replace(/_/g, ' ')}</div>
          <div class="metric-val" style="font-size:0.95rem; color:${res.is_significant ? '#10b981' : '#94a3b8'};">
            p = ${res.p_value} (${res.is_significant ? 'p < 0.05 Sig.' : 'p &ge; 0.05'})
          </div>
        `;
        wilcoxonContainer.appendChild(badge);
      }
    }
  }
}
