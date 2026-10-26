// Hands-free scanning: watch the camera while the cube is turned freely (as a
// whole — no layer turns), grab every face that is held flat and still in the
// grid, recognise repeat views of the same face in any rotation, and once six
// faces are known work out how they fit together into a valid cube.
import { rgbToLab } from './colors.js';
import { resolveLayout, rotate } from './layout.js';

const MOTION = 14;          // max per-cell Lab change between frames while "still"
const SPREAD_MAX = 45;      // max colour spread inside a cell (straddling a gap / blur)
const STILL_MS = 450;       // hold time before recognising a face seen before
const NEW_FACE_MS = 800;    // longer hold before trusting a brand-new face
const AGREE = 22;           // Lab distance under which two sticker readings agree
const MIN_AGREE = 7;        // cells (of 9) that must agree to call it the same face
const MAX_CANDIDATES = 12;

export { rotate };

const dist = (a, b) => Math.hypot((a[0] - b[0]) * 0.5, a[1] - b[1], a[2] - b[2]);

// How many of the 9 cells of rgb (an observation, already rotated) agree with a
// known face. A face looks brighter or darker as it turns towards or away from
// the light, so the observation is first scaled to the face's overall brightness.
function agreement(rgb, face, threshold = AGREE) {
  let num = 0, den = 0;
  rgb.forEach((c, i) => c.forEach((v, ch) => { num += v * face.rgb[i][ch]; den += v * v; }));
  const gain = Math.min(2, Math.max(0.5, den ? num / den : 1));
  const labs = rgb.map(c => rgbToLab(c.map(v => Math.min(255, v * gain))));
  return {
    cells: labs.filter((l, i) => dist(l, face.lab[i]) < threshold).length,
    centre: dist(labs[4], face.lab[4]) < threshold,
  };
}
const medianOf = vals => { const s = [...vals].sort((a, b) => a - b); return s[s.length >> 1]; };

class Face {
  constructor(rgb) { this.obs = [rgb]; this.update(); }
  add(rgb) { this.obs.push(rgb); if (this.obs.length > 15) this.obs.shift(); this.update(); }
  update() {
    this.rgb = Array.from({ length: 9 }, (_, i) => [0, 1, 2].map(ch => medianOf(this.obs.map(o => o[i][ch]))));
    this.lab = this.rgb.map(rgbToLab);
  }
  get count() { return this.obs.length; }
}

export class AutoScan {
  constructor() { this.reset(); }

  reset() {
    this.candidates = [];
    this.prev = null;
    this.stillSince = 0;
    this.buffer = [];
    this.handled = false;     // already acted on the current still period
    this.result = null;
    this.status = 'Hold the cube so one face fills the grid.';
    this.steady = false;
  }

  // The six most-observed candidate faces, skipping any that look like a
  // duplicate of one already chosen (a repeat view that wasn't recognised).
  get faces() {
    const chosen = [];
    for (const c of [...this.candidates].sort((a, b) => b.count - a.count)) {
      const dup = chosen.some(f => [0, 1, 2, 3].some(k => {
        const a = agreement(rotate(c.rgb, k), f);
        return a.centre && a.cells >= MIN_AGREE;
      }));
      if (!dup) chosen.push(c);
      if (chosen.length === 6) break;
    }
    return chosen;
  }

  // Feed one camera sample: 9 rgb colours and each cell's colour spread.
  // Returns true when the set of known faces changed.
  offer(colours, spreads, t, force = false) {
    if (this.result?.valid) return false;
    const labs = colours.map(rgbToLab);
    const moved = !this.prev || labs.some((l, i) => dist(l, this.prev[i]) > MOTION);
    this.prev = labs;
    const flat = spreads.every(s => s < SPREAD_MAX);
    if (moved || !flat) {
      this.stillSince = t; this.buffer = []; this.handled = false; this.steady = false;
      if (!force) {
        this.status = flat ? 'Hold still…' : 'Line one face up with the grid.';
        return false;
      }
    }
    this.buffer.push(colours);
    if (this.buffer.length > 20) this.buffer.shift();
    this.steady = flat;
    if (this.handled && !force) return false;

    const avg = Array.from({ length: 9 }, (_, i) => [0, 1, 2].map(ch =>
      this.buffer.reduce((s, c) => s + c[i][ch], 0) / this.buffer.length));
    const avgLab = avg.map(rgbToLab);
    const held = t - this.stillSince;

    if (!force && avgLab.every(l => dist(l, avgLab[4]) < AGREE)) {
      this.status = 'All nine cells look the same — if that really is a face, press Capture.';
      return false;
    }

    // Compare with every known face in every rotation.
    let best = null;
    for (const face of this.candidates) {
      for (let k = 0; k < 4; k++) {
        const a = agreement(rotate(avg, k), face);
        if (a.centre && (!best || a.cells > best.agree)) best = { face, k, agree: a.cells };
      }
    }

    if (best && best.agree >= MIN_AGREE) {
      if (held < STILL_MS && !force) { this.status = 'Hold still…'; return false; }
      best.face.add(rotate(avg, best.k));
      this.handled = true;
      const n = this.faces.indexOf(best.face) + 1;
      this.status = n ? `Seen face ${n} again ✓ — keep turning the cube.` : 'Seen that face again.';
      return this.afterChange();
    }
    if (held < NEW_FACE_MS && !force) { this.status = 'Hold still…'; return false; }
    this.handled = true;
    if (this.candidates.length >= MAX_CANDIDATES) {
      this.status = "That doesn't match any face seen so far. If the cube was twisted, press Start over.";
      return false;
    }
    this.candidates.push(new Face(avg));
    this.status = `New face found (${this.faces.length} of 6) — keep turning the cube.`;
    return this.afterChange();
  }

  afterChange() {
    if (this.faces.length === 6) {
      this.result = resolveLayout(this.faces.map(f => f.rgb));
      const n = this.result.fixed.length;
      this.status = !this.result.valid
        ? "All six faces seen, but they don't fit together yet — keep showing faces so misread stickers can be corrected, or fix them in the net."
        : n ? `Got the whole cube! ${n} stickers looked misread and were corrected (outlined in the net) — please check them.`
        : 'Got the whole cube! Check the net, then press Solve.';
    }
    return true;
  }
}
