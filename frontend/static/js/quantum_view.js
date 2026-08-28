/**
 * Quantum State Inspector & Wave Function Canvas Visualizer
 */

class QuantumView {
  constructor(canvasId) {
    this.canvas = document.getElementById(canvasId);
    this.ctx = this.canvas ? this.canvas.getContext('2d') : null;
    this.alpha = 0.8;
    this.mbest = 0.0;
    this.particles = [];
    this.timeTick = 0;

    if (this.canvas) {
      this.resizeCanvas();
      window.addEventListener('resize', () => this.resizeCanvas());
      this.animate();
    }
  }

  resizeCanvas() {
    if (!this.canvas) return;
    this.canvas.width = this.canvas.parentElement.clientWidth - 16;
    this.canvas.height = 140;
  }

  updateQuantumState(state) {
    if (state.alpha !== undefined) this.alpha = state.alpha;
    if (state.mbest_norm !== undefined) this.mbest = state.mbest_norm;
    if (state.quantum_dispersion !== undefined) {
      // Generate sample particle positions around mbest
      this.particles = [];
      const count = 12;
      for (let i = 0; i < count; i++) {
        const u = Math.random();
        const sign = Math.random() > 0.5 ? 1 : -1;
        const offset = sign * this.alpha * Math.log(1.0 / Math.max(0.001, u)) * 15.0;
        this.particles.push(offset);
      }
    }
  }

  animate() {
    this.render();
    this.timeTick += 0.05;
    requestAnimationFrame(() => this.animate());
  }

  render() {
    if (!this.ctx || !this.canvas) return;
    const w = this.canvas.width;
    const h = this.canvas.height;
    const ctx = this.ctx;

    ctx.clearRect(0, 0, w, h);

    // 1. Background Grid Lines
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.05)';
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(0, h / 2);
    ctx.lineTo(w, h / 2);
    ctx.moveTo(w / 2, 0);
    ctx.lineTo(w / 2, h);
    ctx.stroke();

    const centerX = w / 2;
    const centerY = h - 20;

    // 2. Draw Delta Potential Well Wave Function: psi(x) = exp(-|x| / L)
    const L = Math.max(10, this.alpha * 55);
    ctx.beginPath();
    ctx.strokeStyle = '#06b6d4';
    ctx.lineWidth = 2.5;
    ctx.shadowBlur = 10;
    ctx.shadowColor = '#06b6d4';

    for (let x = -w / 2; x <= w / 2; x += 3) {
      const psi = Math.exp(-Math.abs(x) / L);
      const y = centerY - psi * (h - 40);
      if (x === -w / 2) ctx.moveTo(centerX + x, y);
      else ctx.lineTo(centerX + x, y);
    }
    ctx.stroke();
    ctx.shadowBlur = 0; // Reset shadow

    // 3. Fill Gradient under wave function
    const grad = ctx.createLinearGradient(0, 0, 0, h);
    grad.addColorStop(0, 'rgba(6, 182, 212, 0.35)');
    grad.addColorStop(1, 'rgba(6, 182, 212, 0.0)');
    ctx.lineTo(w, centerY);
    ctx.lineTo(0, centerY);
    ctx.closePath();
    ctx.fillStyle = grad;
    ctx.fill();

    // 4. Draw Delta-Well Spike at Origin
    ctx.strokeStyle = '#f59e0b';
    ctx.lineWidth = 2;
    ctx.setLineDash([3, 3]);
    ctx.beginPath();
    ctx.moveTo(centerX, 15);
    ctx.lineTo(centerX, centerY);
    ctx.stroke();
    ctx.setLineDash([]);

    // 5. Draw Superposed Particles
    ctx.fillStyle = '#a855f7';
    this.particles.forEach((offset, idx) => {
      const px = centerX + offset + Math.sin(this.timeTick + idx) * 2;
      const psi = Math.exp(-Math.abs(offset) / L);
      const py = centerY - psi * (h - 40);

      ctx.beginPath();
      ctx.arc(px, py, 3.5, 0, 2 * Math.PI);
      ctx.fill();
    });

    // 6. Draw Labels & Parameters
    ctx.fillStyle = '#94a3b8';
    ctx.font = '10px -apple-system, sans-serif';
    ctx.fillText(`ψ(x) Wave Function in δ-Well | α = ${this.alpha.toFixed(3)}`, 10, 16);
    ctx.fillStyle = '#06b6d4';
    ctx.fillText(`mbest Attractor [x=0]`, centerX + 6, 26);
  }
}
