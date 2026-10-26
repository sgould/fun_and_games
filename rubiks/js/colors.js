// Turning camera samples into sticker colours.
// Each face's centre sticker defines that face's colour. Once all six faces are
// scanned, every other sticker is matched to a centre with an optimal assignment
// that forces exactly nine stickers per colour, which separates the usual
// confusions (white/yellow, red/orange) far better than per-sticker thresholds.
import { FACES } from './cubemodel.js';

export const STANDARD = {
  white: '#f4f4f4', yellow: '#ffd500', red: '#c41e3a',
  orange: '#ff6a00', green: '#009e60', blue: '#0051ba',
};
// Typical webcam appearance of each colour, used only to name the centres.
const TYPICAL = {
  white: [225, 225, 220], yellow: [215, 205, 50], red: [185, 35, 45],
  orange: [240, 115, 35], green: [35, 160, 80], blue: [25, 75, 180],
};
export const DEFAULT_SCHEME = { U: 'white', R: 'red', F: 'green', D: 'yellow', L: 'orange', B: 'blue' };

export function rgbToLab([r, g, b]) {
  const lin = v => { v /= 255; return v > 0.04045 ? ((v + 0.055) / 1.055) ** 2.4 : v / 12.92; };
  const R = lin(r), G = lin(g), B = lin(b);
  const f = t => t > 0.008856 ? Math.cbrt(t) : 7.787 * t + 16 / 116;
  const X = f((R * 0.4124 + G * 0.3576 + B * 0.1805) / 0.95047);
  const Y = f(R * 0.2126 + G * 0.7152 + B * 0.0722);
  const Z = f((R * 0.0193 + G * 0.1192 + B * 0.9505) / 1.08883);
  return [116 * Y - 16, 500 * (X - Y), 200 * (Y - Z)];
}

// Lightness varies a lot with shading and glare, so it counts for less than hue.
function labDist(a, b, lWeight = 0.5) {
  return Math.hypot((a[0] - b[0]) * lWeight, a[1] - b[1], a[2] - b[2]);
}

// Minimum-cost assignment for a square cost matrix; returns column for each row.
export function hungarian(cost) {
  const n = cost.length, INF = Infinity;
  const u = Array(n + 1).fill(0), v = Array(n + 1).fill(0);
  const p = Array(n + 1).fill(0), way = Array(n + 1).fill(0);
  for (let i = 1; i <= n; i++) {
    p[0] = i;
    let j0 = 0;
    const minv = Array(n + 1).fill(INF), used = Array(n + 1).fill(false);
    do {
      used[j0] = true;
      const i0 = p[j0];
      let delta = INF, j1 = 0;
      for (let j = 1; j <= n; j++) {
        if (used[j]) continue;
        const cur = cost[i0 - 1][j - 1] - u[i0] - v[j];
        if (cur < minv[j]) { minv[j] = cur; way[j] = j0; }
        if (minv[j] < delta) { delta = minv[j]; j1 = j; }
      }
      for (let j = 0; j <= n; j++) {
        if (used[j]) { u[p[j]] += delta; v[j] -= delta; } else minv[j] -= delta;
      }
      j0 = j1;
    } while (p[j0] !== 0);
    do { const j1 = way[j0]; p[j0] = p[j1]; j0 = j1; } while (j0);
  }
  const ans = Array(n);
  for (let j = 1; j <= n; j++) ans[p[j] - 1] = j - 1;
  return ans;
}

// scans: { face: [9 x [r,g,b]] } for the faces scanned so far.
// Returns { face: [9 face letters] }.
export function classify(scans) {
  const faces = FACES.split('').filter(f => scans[f]);
  const labs = Object.fromEntries(faces.map(f => [f, scans[f].map(rgbToLab)]));
  const items = [];
  faces.forEach(f => { for (let i = 0; i < 9; i++) if (i !== 4) items.push([f, i]); });
  const result = Object.fromEntries(faces.map(f => [f, Array(9).fill(f)]));
  let means = Object.fromEntries(faces.map(f => [f, labs[f][4]]));

  for (let iter = 0; iter < 4; iter++) {
    if (faces.length === 6) {
      const cols = FACES.split('').flatMap(c => Array(8).fill(c));
      const cost = items.map(([f, i]) => cols.map(c => labDist(labs[f][i], means[c])));
      const asg = hungarian(cost);
      items.forEach(([f, i], r) => { result[f][i] = cols[asg[r]]; });
    } else {
      for (const [f, i] of items) {
        result[f][i] = faces.reduce((best, c) =>
          labDist(labs[f][i], means[c]) < labDist(labs[f][i], means[best]) ? c : best);
      }
    }
    // Refine each colour's reference using every sticker assigned to it.
    const acc = Object.fromEntries(faces.map(c => [c, [0, 0, 0, 0]]));
    faces.forEach(f => result[f].forEach((c, i) => {
      const a = acc[c], w = i === 4 ? 2 : 1;
      a[0] += labs[f][i][0] * w; a[1] += labs[f][i][1] * w; a[2] += labs[f][i][2] * w; a[3] += w;
    }));
    means = Object.fromEntries(faces.map(c => [c, acc[c].slice(0, 3).map(v => v / acc[c][3])]));
  }
  return result;
}

// Give each face a colour name. centres: { face: [r,g,b] } for scanned faces;
// unscanned faces prefer the standard scheme.
export function nameFaces(centres) {
  const names = Object.keys(TYPICAL);
  const typicalLab = names.map(n => rgbToLab(TYPICAL[n]));
  const faces = FACES.split('');
  const cost = faces.map(f => centres[f]
    ? typicalLab.map(t => labDist(rgbToLab(centres[f]), t, 0.3))
    : names.map(n => (n === DEFAULT_SCHEME[f] ? 0 : 1)));
  const asg = hungarian(cost);
  return Object.fromEntries(faces.map((f, i) => [f, names[asg[i]]]));
}
