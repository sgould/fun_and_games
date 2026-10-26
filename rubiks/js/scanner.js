// Webcam capture with a 3x3 alignment grid. Samples the median colour of the
// middle of each grid cell, averaged over the last few frames.

const GRID_FRACTION = 0.6;   // grid side as a fraction of the shorter frame side
const PATCH = 0.5;           // sampled patch as a fraction of a cell
const HISTORY_MS = 400;     // average samples from this recent window

function gridRect(w, h) {
  const side = GRID_FRACTION * Math.min(w, h);
  return { x: (w - side) / 2, y: (h - side) / 2, side, cell: side / 3 };
}

function median(values) {
  values.sort((a, b) => a - b);
  return values[values.length >> 1];
}

export class Scanner {
  constructor(canvas) {
    this.canvas = canvas;
    this.ctx = canvas.getContext('2d');
    this.video = document.createElement('video');
    this.video.playsInline = true;
    this.video.muted = true;
    this.off = document.createElement('canvas');
    this.offCtx = this.off.getContext('2d', { willReadFrequently: true });
    this.mirror = true;
    this.hints = {};
    this.gridColor = 'rgba(255,255,255,0.9)';
    this.onSample = null;   // (colours, spreads, time) after every sample        // { top, right, bottom, left } -> css colour, in true (unmirrored) sides
    this.history = [];
    this.flash = 0;
    this.lastSample = 0;
    this.stream = null;
    requestAnimationFrame(t => this.draw(t));
  }

  async start(deviceId) {
    this.stop();
    this.stream = await navigator.mediaDevices.getUserMedia({
      video: deviceId ? { deviceId: { exact: deviceId } } : { width: { ideal: 1280 }, height: { ideal: 720 } },
      audio: false,
    });
    this.video.srcObject = this.stream;
    await this.video.play();
  }

  stop() {
    this.stream?.getTracks().forEach(t => t.stop());
    this.stream = null;
    this.history = [];
  }

  get ready() { return this.video.readyState >= 2 && this.history.length > 0; }

  // Current 9 colours (row-major as seen by the camera), averaged over recent frames.
  current() {
    if (!this.history.length) return null;
    const frames = this.history.map(h => h.frame);
    return Array.from({ length: 9 }, (_, i) => [0, 1, 2].map(ch =>
      frames.reduce((s, frame) => s + frame[i][ch], 0) / frames.length));
  }

  capture() {
    if (this.video.readyState < 2 || !this.stream) return null;
    this.sample();
    const colours = this.current();
    if (colours) this.flash = 1;
    return colours;
  }

  sample() {
    const v = this.video;
    const W = 320, H = Math.round(W * v.videoHeight / v.videoWidth);
    this.off.width = W; this.off.height = H;
    this.offCtx.drawImage(v, 0, 0, W, H);
    const data = this.offCtx.getImageData(0, 0, W, H).data;
    const g = gridRect(W, H), inset = g.cell * (1 - PATCH) / 2;
    const frame = [], spread = [];
    for (let r = 0; r < 3; r++) for (let c = 0; c < 3; c++) {
      const x0 = Math.round(g.x + c * g.cell + inset), y0 = Math.round(g.y + r * g.cell + inset);
      const n = Math.round(g.cell * PATCH);
      const ch = [[], [], []];
      for (let y = y0; y < y0 + n; y += 2) for (let x = x0; x < x0 + n; x += 2) {
        const k = (y * W + x) * 4;
        ch[0].push(data[k]); ch[1].push(data[k + 1]); ch[2].push(data[k + 2]);
      }
      frame.push(ch.map(median));
      // 20th-80th percentile range: small on a single sticker, large across a gap or blur.
      spread.push(Math.max(...ch.map(a => a[Math.floor(a.length * 0.8)] - a[Math.floor(a.length * 0.2)])));
    }
    const now = performance.now();
    this.history.push({ t: now, frame });
    this.history = this.history.filter(h => now - h.t <= HISTORY_MS);
    this.onSample?.(frame, spread, now);
  }

  draw(t) {
    requestAnimationFrame(tt => this.draw(tt));
    const v = this.video, ctx = this.ctx;
    if (v.readyState < 2 || !this.stream) return;
    if (t - this.lastSample > 80) { this.sample(); this.lastSample = t; }

    const w = v.videoWidth, h = v.videoHeight;
    if (this.canvas.width !== w || this.canvas.height !== h) { this.canvas.width = w; this.canvas.height = h; }
    ctx.save();
    if (this.mirror) { ctx.translate(w, 0); ctx.scale(-1, 1); }
    ctx.drawImage(v, 0, 0, w, h);

    // Everything below is drawn in camera coordinates, so it mirrors with the video.
    const g = gridRect(w, h);
    ctx.fillStyle = 'rgba(0,0,0,0.35)';
    ctx.fillRect(0, 0, w, g.y); ctx.fillRect(0, g.y + g.side, w, h - g.y - g.side);
    ctx.fillRect(0, g.y, g.x, g.side); ctx.fillRect(g.x + g.side, g.y, w - g.x - g.side, g.side);

    const bar = Math.max(8, g.cell * 0.12), gap = bar * 0.8;
    const sides = {
      top: [g.x, g.y - gap - bar, g.side, bar], bottom: [g.x, g.y + g.side + gap, g.side, bar],
      left: [g.x - gap - bar, g.y, bar, g.side], right: [g.x + g.side + gap, g.y, bar, g.side],
    };
    for (const [side, rect] of Object.entries(sides)) {
      if (!this.hints[side]) continue;
      ctx.fillStyle = this.hints[side];
      ctx.strokeStyle = '#000'; ctx.lineWidth = 2;
      ctx.fillRect(...rect); ctx.strokeRect(...rect);
    }

    ctx.lineWidth = Math.max(2, w / 400);
    ctx.strokeStyle = this.gridColor;
    ctx.shadowColor = 'rgba(0,0,0,0.8)'; ctx.shadowBlur = 4;
    ctx.beginPath();
    for (let i = 0; i <= 3; i++) {
      ctx.moveTo(g.x + i * g.cell, g.y); ctx.lineTo(g.x + i * g.cell, g.y + g.side);
      ctx.moveTo(g.x, g.y + i * g.cell); ctx.lineTo(g.x + g.side, g.y + i * g.cell);
    }
    ctx.stroke();
    ctx.shadowBlur = 0;

    const colours = this.current();
    if (colours) {
      const s = g.cell * 0.28;
      colours.forEach((rgb, i) => {
        const cx = g.x + (i % 3 + 0.5) * g.cell, cy = g.y + (Math.floor(i / 3) + 0.5) * g.cell;
        ctx.fillStyle = `rgb(${rgb.map(Math.round).join(',')})`;
        ctx.fillRect(cx - s / 2, cy - s / 2, s, s);
        ctx.strokeStyle = '#fff'; ctx.lineWidth = 2; ctx.strokeRect(cx - s / 2, cy - s / 2, s, s);
      });
    }
    ctx.restore();

    if (this.flash > 0) {
      ctx.fillStyle = `rgba(255,255,255,${this.flash * 0.6})`;
      ctx.fillRect(0, 0, w, h);
      this.flash = Math.max(0, this.flash - 0.08);
    }
  }
}
