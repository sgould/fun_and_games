// Fitting six scanned faces together into a cube that can actually exist.
//
// Faces may have been scanned into the wrong slot or the wrong way up, and a
// sticker or two may have been misread. We try every arrangement of the faces
// (30, up to whole-cube rotation) with every rotation of each face (4^6) and
// keep the first that forms a valid cube. If none does, we take the closest
// placements and look for the smallest set of swapped sticker colours that makes
// them valid — colours are assigned nine per colour, so misreads come in pairs.
import { rgbToLab, classify, nameFaces } from './colors.js';
import { validate } from './validate.js';
import { FACES } from './cubemodel.js';

const TOP_PLACEMENTS = 6;     // near-miss placements to try repairing
const DOUBLE_SWAP_PLACEMENTS = 3;
const CLEAR_WIN = 15;          // cost margin (Lab units) for a correction to count as certain

// Rotate a 3x3 row-major array a quarter turn clockwise, k times.
export function rotate(a, k = 1) {
  let r = a;
  for (let i = 0; i < ((k % 4) + 4) % 4; i++) r = [r[6], r[3], r[0], r[7], r[4], r[1], r[8], r[5], r[2]];
  return r;
}

const CORNERS = [[8, 9, 20], [6, 18, 38], [0, 36, 47], [2, 45, 11], [29, 26, 15], [27, 44, 24], [33, 53, 42], [35, 17, 51]];
const CORNER_SET = new Set(['URF', 'UFL', 'ULB', 'UBR', 'DFR', 'DLF', 'DBL', 'DRB']
  .flatMap(c => [c, c[1] + c[2] + c[0], c[2] + c[0] + c[1]]));
const EDGES = [[5, 10], [7, 19], [3, 37], [1, 46], [32, 16], [28, 25], [30, 43], [34, 52], [23, 12], [21, 41], [50, 39], [48, 14]];
const EDGE_SET = new Set(['UR', 'UF', 'UL', 'UB', 'DR', 'DF', 'DL', 'DB', 'FR', 'FL', 'BL', 'BR'].flatMap(e => [e, e[1] + e[0]]));
const PIECES = [...CORNERS, ...EDGES];

// Number of distinct, real pieces (max 8 corners + 12 edges = 20).
function score(fl) {
  const seen = new Set();
  for (const p of PIECES) {
    const s = p.map(i => fl[i]).join('');
    if ((p.length === 3 ? CORNER_SET : EDGE_SET).has(s)) seen.add([...s].sort().join(''));
  }
  return seen.size;
}

// Sticker positions belonging to pieces that are invalid or appear twice.
function suspects(fl) {
  const byKey = new Map(), bad = new Set();
  for (const p of PIECES) {
    const s = p.map(i => fl[i]).join('');
    if (!(p.length === 3 ? CORNER_SET : EDGE_SET).has(s)) { p.forEach(i => bad.add(i)); continue; }
    const key = [...s].sort().join('');
    if (byKey.has(key)) { p.forEach(i => bad.add(i)); byKey.get(key).forEach(i => bad.add(i)); }
    else byKey.set(key, p);
  }
  return [...bad];
}

const isValid = fl => score(fl) === 20 && validate(fl.join('')) === null;

// The 30 distinct ways to put six colours on a cube (up to whole-cube rotation),
// as position -> item lists. order[0] always goes on U, the next one on F.
function* arrangements(order) {
  const [u, ...rest] = order;
  for (const d of rest) {
    const [f, ...others] = rest.filter(x => x !== d);   // spin about U-D so f is at F
    for (const [r, b, l] of permutations(others)) yield [u, r, f, d, l, b];
  }
}

function permutations(a) {
  if (a.length <= 1) return [a];
  return a.flatMap((x, i) => permutations([...a.slice(0, i), ...a.slice(i + 1)]).map(p => [x, ...p]));
}

// observed: six arrays of 9 rgb samples, in any order and rotation.
// Returns { valid, uncertain, faces: { U: 9 rgb, ... }, letters: 54-char string, fixed: [facelet indices] }.
// faces are placed and rotated into standard orientation; letters is the cube
// including any corrected stickers (listed in fixed); uncertain means another
// correction fitted the colours almost as well.
export function resolveLayout(observed) {
  const tmp = Object.fromEntries(FACES.split('').map((f, i) => [f, observed[i]]));
  const labelled = classify(tmp);
  const clusters = FACES.split('').map(f => labelled[f].map(l => FACES.indexOf(l)));

  // Try the friendliest orientation first: white on top, green in front.
  const names = nameFaces(Object.fromEntries(FACES.split('').map((f, i) => [f, observed[i][4]])));
  const pref = ['white', 'green', 'red', 'blue', 'orange', 'yellow'];
  const order = [0, 1, 2, 3, 4, 5].sort((a, b) => pref.indexOf(names[FACES[a]]) - pref.indexOf(names[FACES[b]]));

  const top = [];   // best near-miss placements, highest score first
  for (const arr of arrangements(order)) {
    const letterOf = Array(6);
    arr.forEach((obsIdx, pos) => { letterOf[obsIdx] = FACES[pos]; });
    for (let combo = 0; combo < 4096; combo++) {
      const fl = Array(54);
      for (let pos = 0; pos < 6; pos++) {
        const stickers = rotate(clusters[arr[pos]], (combo >> (pos * 2)) & 3);
        for (let k = 0; k < 9; k++) fl[pos * 9 + k] = letterOf[stickers[k]];
      }
      const s = score(fl);
      if (top.length === TOP_PLACEMENTS && s <= top[top.length - 1].score && s < 20) continue;
      if (s === 20 && validate(fl.join('')) === null) return result(observed, arr, combo, fl, []);
      top.push({ score: s, arr, combo, fl });
      top.sort((a, b) => b.score - a.score);
      if (top.length > TOP_PLACEMENTS) top.pop();
    }
  }

  // No placement fits as read: look for misread stickers.
  const fixes = top.flatMap((p, rank) => {
    const faces = placedFaces(observed, p.arr, p.combo);
    const labs = FACES.split('').flatMap(f => faces[f].map(rgbToLab));
    return repairs(p.fl, labs, rank < DOUBLE_SWAP_PLACEMENTS).map(fix => ({ p, fix }));
  }).sort((a, b) => a.fix.cost - b.fix.cost);
  if (fixes.length) {
    const [best, runnerUp] = fixes;
    const uncertain = !!runnerUp && runnerUp.fix.cost - best.fix.cost < CLEAR_WIN;
    return { ...result(observed, best.p.arr, best.p.combo, best.fix.fl, best.fix.changed), uncertain };
  }
  const p = top[0];
  return { ...result(observed, p.arr, p.combo, p.fl, []), valid: false };
}

function placedFaces(observed, arr, combo) {
  return Object.fromEntries(FACES.split('').map((f, pos) =>
    [f, rotate(observed[arr[pos]], (combo >> (pos * 2)) & 3)]));
}

function result(observed, arr, combo, fl, fixed) {
  return { valid: true, uncertain: false, faces: placedFaces(observed, arr, combo), letters: fl.join(''), fixed };
}

// Valid repairs of fl by one or two colour swaps, cheapest first, judged by how
// well each sticker's camera colour matches its new colour. Returns at most two.
function repairs(fl, labs, allowDouble) {
  const dist = (a, b) => Math.hypot((a[0] - b[0]) * 0.5, a[1] - b[1], a[2] - b[2]);
  const mean = {};
  for (const f of FACES) {
    const idx = fl.map((l, i) => (l === f ? i : -1)).filter(i => i >= 0);
    mean[f] = [0, 1, 2].map(ch => idx.reduce((s, i) => s + labs[i][ch], 0) / idx.length);
  }
  const fit = (i, letter) => dist(labs[i], mean[letter]);
  const nonCentre = [...Array(54).keys()].filter(i => i % 9 !== 4);
  const sus = suspects(fl);
  const first = sus.length ? sus : nonCentre;

  // Candidate swaps touching a suspect sticker, cheapest first.
  const swaps = [];
  const seen = new Set();
  for (const i of first) for (const j of nonCentre) {
    if (fl[i] === fl[j]) continue;
    const key = i < j ? i * 54 + j : j * 54 + i;
    if (seen.has(key)) continue;
    seen.add(key);
    swaps.push({ i, j, cost: fit(i, fl[j]) + fit(j, fl[i]) - fit(i, fl[i]) - fit(j, fl[j]) });
  }
  swaps.sort((a, b) => a.cost - b.cost);

  const apply = list => {
    const out = [...fl];
    for (const { i, j } of list) [out[i], out[j]] = [out[j], out[i]];
    return out;
  };
  const found = [];
  const keep = (list, cost) => {
    found.push({ fl: apply(list), cost, changed: list.flatMap(x => [x.i, x.j]) });
    found.sort((a, b) => a.cost - b.cost);
    if (found.length > 2) found.pop();
  };
  const worst = () => (found.length < 2 ? Infinity : found[1].cost);

  for (const s of swaps) {
    if (s.cost >= worst()) break;
    if (isValid(apply([s]))) keep([s], s.cost);
  }
  if (allowDouble) {
    // Real misreads are among the cheapest swaps, so pair only those.
    const cand = swaps.slice(0, 120);
    for (let a = 0; a < cand.length; a++) {
      for (let b = a + 1; b < cand.length; b++) {
        const cost = cand[a].cost + cand[b].cost;
        if (cost >= worst()) break;
        const pair = [cand[a], cand[b]];
        if (new Set([pair[0].i, pair[0].j, pair[1].i, pair[1].j]).size < 4) continue;
        if (isValid(apply(pair))) keep(pair, cost);
      }
    }
  }
  return found;
}
