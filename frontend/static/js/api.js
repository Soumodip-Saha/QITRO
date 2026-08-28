/**
 * QITRO API & WebSocket Communication Layer
 */

const API = {
  async getCityPresets() {
    const res = await fetch('/api/city-presets');
    return await res.json();
  },

  async getCityGraph(cityId) {
    const res = await fetch(`/api/city-graph/${cityId}`);
    return await res.json();
  },

  async optimize(payload) {
    const res = await fetch('/api/optimize', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Optimization failed');
    }
    return await res.json();
  },

  async runBenchmark(payload) {
    const res = await fetch('/api/benchmark', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Benchmark execution failed');
    }
    return await res.json();
  },

  async addIncident(payload) {
    const res = await fetch('/api/incident', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    return await res.json();
  },

  async removeIncident(incidentId) {
    const res = await fetch(`/api/incident/${incidentId}`, { method: 'DELETE' });
    return await res.json();
  },

  async startSimulation() {
    const res = await fetch('/api/simulation/start', { method: 'POST' });
    return await res.json();
  },

  async stepSimulation() {
    const res = await fetch('/api/simulation/step', { method: 'POST' });
    return await res.json();
  },

  async getConvergenceProfile(payload) {
    const res = await fetch('/api/analytics/convergence-profile', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    return await res.json();
  },

  async runHypothesisTesting(payload) {
    const res = await fetch('/api/analytics/hypothesis-testing', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    return await res.json();
  },

  async getScalabilityProfile(payload) {
    const res = await fetch('/api/analytics/scalability-profile', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    return await res.json();
  },

  async getQuantumMathTheory() {
    const res = await fetch('/api/theory/quantum-math');
    return await res.json();
  },

  getExportUrl(format = 'json') {
    return `/api/export-report?format=${format}`;
  }
};

class LiveWebSocketClient {
  constructor(onMessageCallback) {
    this.onMessage = onMessageCallback;
    this.ws = null;
    this.connect();
  }

  connect() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/live-stream`;
    this.ws = new WebSocket(wsUrl);

    this.ws.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data);
        if (this.onMessage) {
          this.onMessage(payload);
        }
      } catch (e) {
        console.error('WS Parse Error:', e);
      }
    };

    this.ws.onclose = () => {
      setTimeout(() => this.connect(), 2000);
    };
  }

  send(data) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data));
    }
  }
}
