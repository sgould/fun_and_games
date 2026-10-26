import { Scanner } from './scanner.js';
import { AutoScan } from './autoscan.js';
import { resolveLayout } from './layout.js';
import { Viewer } from './viewer.js';
import { classify, nameFaces, STANDARD } from './colors.js';
import { validate } from './validate.js';
import { invertMove, FACES } from './cubemodel.js';

const ORDER = ['F', 'R', 'B', 'L', 'U', 'D'];
const FACE_NAMES = { U: 'Up', R: 'Right', F: 'Front', D: 'Down', L: 'Left', B: 'Back' };
// Neighbouring face on each side of the grid while scanning a face (camera view).
const NEIGHBOURS = {
  F: { top: 'U', right: 'R', bottom: 'D', left: 'L' },
  R: { top: 'U', right: 'B', bottom: 'D', left: 'F' },
  B: { top: 'U', right: 'L', bottom: 'D', left: 'R' },
  L: { top: 'U', right: 'F', bottom: 'D', left: 'B' },
  U: { top: 'B', right: 'R', bottom: 'F', left: 'L' },
  D: { top: 'F', right: 'R', bottom: 'B', left: 'L' },
};

const $ = id => document.getElementById(id);
const state = {
  scans: {},        // face -> 9 rgb samples
  manual: {},       // face -> true when filled in by hand
  auto: {},         // face -> 9 letters from the classifier
  overrides: {},    // facelet index -> letter set by clicking the net
  names: nameFaces({}),
  current: 'F',
  paint: 'U',
  mode: 'auto',     // 'auto': just turn the cube; 'guided': face by face
  fixed: new Set(), // facelet indices corrected by the layout search
  uncertain: false, // the search's corrections were a close call
  layoutNote: '',   // what the layout search changed, shown under the net
};
const solver = { ready: false, scrambled: null, moves: [], index: 0, playing: false, busy: false };

const scanner = new Scanner($('camera'));
const viewer = new Viewer($('viewer'));
const autoScan = new AutoScan();

const known = f => !!(state.scans[f] || state.manual[f]);
const hex = f => STANDARD[state.names[f]];
const colourName = f => state.names[f];

function facelet(i) {
  if (state.overrides[i]) return state.overrides[i];
  const f = FACES[Math.floor(i / 9)], k = i % 9;
  if (k === 4) return known(f) ? f : null;
  return state.auto[f]?.[k] ?? null;
}
const facelets = () => Array.from({ length: 54 }, (_, i) => facelet(i));

// ---------- scanning ----------

function recompute() {
  state.auto = classify(state.scans);
  state.names = nameFaces(Object.fromEntries(Object.entries(state.scans).map(([f, s]) => [f, s[4]])));
  renderAll();
}

function instructions(face) {
  const side = scanner.mirror ? 'right' : 'left';
  const nm = f => known(f) ? `<b style="color:${hex(f)}">${colourName(f)}</b>` : `the ${FACE_NAMES[f].toLowerCase()}`;
  switch (face) {
    case 'F': return 'Hold the cube up to the camera so one face fills the grid. This is the <b>front</b>. ' +
      'Note which colour is on top and <b>keep it on top</b> for the next four faces.';
    case 'R': return `Turn the whole cube a quarter turn so the ${nm('F')} face moves to the <b>${side}</b> of the screen. Same colour on top.`;
    case 'B': return `Turn again so the ${nm('R')} face moves to the <b>${side}</b> of the screen. Same colour on top.`;
    case 'L': return `Turn again so the ${nm('B')} face moves to the <b>${side}</b> of the screen. Same colour on top.`;
    case 'U': return `Turn once more so ${nm('F')} faces the camera again, then tip the <b>top</b> towards the camera — ${nm('F')} should be at the <b>bottom</b> of the screen.`;
    case 'D': return `Tip it back so ${nm('F')} faces the camera, then tip the <b>bottom</b> towards the camera — ${nm('F')} should be at the <b>top</b> of the screen.`;
  }
}

function updateScanUI() {
  const auto = state.mode === 'auto';
  $('guided').hidden = auto;
  $('auto').hidden = !auto;
  document.querySelectorAll('#mode button').forEach(b => b.classList.toggle('active', b.dataset.mode === state.mode));
  $('capture').innerHTML = (auto ? '📷 Capture now' : '📷 Capture face') + ' <kbd>Space</kbd>';
  if (auto) { scanner.hints = {}; renderAuto(); return; }
  const f = state.current;
  $('step-title').textContent = `Step ${ORDER.indexOf(f) + 1} of 6 — ${FACE_NAMES[f]} face`;
  $('step-text').innerHTML = instructions(f) +
    '<br><span class="muted">Coloured bars around the grid show which centre colour should sit next to each edge.</span>';
  $('chips').innerHTML = ORDER.map(o => `<button class="chip ${o === f ? 'active' : ''} ${known(o) ? 'done' : ''}"
      data-face="${o}" style="--c:${known(o) ? hex(o) : 'transparent'}">${FACE_NAMES[o]}</button>`).join('');
  const hints = {};
  for (const [side, nf] of Object.entries(NEIGHBOURS[f])) if (known(nf)) hints[side] = hex(nf);
  scanner.hints = hints;
}

function capture() {
  const colours = scanner.capture();
  if (!colours) return;
  if (state.mode === 'auto') {
    if (autoScan.offer(colours, Array(9).fill(0), performance.now(), true)) applyAuto();
    renderAuto();
    return;
  }
  const f = state.current;
  state.scans[f] = colours;
  delete state.manual[f];
  for (let k = 0; k < 9; k++) delete state.overrides[FACES.indexOf(f) * 9 + k];
  const next = ORDER.find(o => !known(o) && o !== f) ?? ORDER[(ORDER.indexOf(f) + 1) % 6];
  if (Object.keys(state.scans).length < 6 || !known(next)) state.current = next;
  state.fixed.clear();
  state.layoutNote = '';
  recompute();
  if (Object.keys(state.scans).length === 6 && validate(facelets().join('')) !== null) findLayout();
}

// The six scanned faces don't make a possible cube as placed: search other face
// positions and rotations (and likely misread stickers) for one that does.
function findLayout() {
  const res = resolveLayout(FACES.split('').map(f => state.scans[f]));
  if (!res.valid) {
    state.layoutNote = "Couldn't find any arrangement of these faces that makes a possible cube — rescan the faces that look wrong.";
    renderNet();
    return;
  }
  applyLayout(res);
  state.layoutNote = "The faces as scanned didn't make a possible cube, so their positions and rotations were searched to find one that does.";
  renderNet();
}

// Place resolved faces on the cube; corrected stickers become outlined overrides.
function applyLayout(res) {
  state.scans = res.faces;
  state.manual = {};
  state.overrides = {};
  state.auto = classify(state.scans);
  state.names = nameFaces(Object.fromEntries(Object.entries(state.scans).map(([f, s]) => [f, s[4]])));
  state.fixed = new Set(res.fixed);
  for (let i = 0; i < 54; i++) {
    if (facelet(i) !== res.letters[i]) { state.overrides[i] = res.letters[i]; state.fixed.add(i); }
  }
  state.uncertain = res.uncertain;
  renderAll();
}

// ---------- hands-free scanning ----------

scanner.onSample = (colours, spreads, t) => {
  if (state.mode !== 'auto') { scanner.gridColor = 'rgba(255,255,255,0.9)'; return; }
  const changed = autoScan.offer(colours, spreads, t);
  scanner.gridColor = autoScan.result?.valid ? 'rgba(60,207,122,0.95)'
    : autoScan.steady ? 'rgba(255,214,0,0.95)' : 'rgba(255,255,255,0.9)';
  if (changed) { scanner.flash = 1; applyAuto(); }
  renderAuto();
};

// Once six faces are known, place them on the cube and hand over to the net.
function applyAuto() {
  if (!autoScan.result) return;
  state.layoutNote = '';
  applyLayout(autoScan.result);
}

function renderAuto() {
  if (state.mode !== 'auto') return;
  if ($('auto-status').textContent !== autoScan.status) $('auto-status').textContent = autoScan.status;
  $('auto-status').className = autoScan.result?.valid ? 'ok' : '';
  const faces = autoScan.faces;
  const key = faces.map(f => f.count).join() + '|' + autoScan.candidates.length;
  if ($('auto-faces').dataset.key === key) return;
  $('auto-faces').dataset.key = key;
  $('auto-faces').innerHTML = Array.from({ length: 6 }, (_, i) => {
    const f = faces[i];
    if (!f) return '<div class="mini empty"></div>';
    return `<div class="mini" title="Seen ${f.count} time${f.count > 1 ? 's' : ''}">${f.rgb.map(c =>
      `<span style="background:rgb(${c.map(Math.round).join(',')})"></span>`).join('')}<em>${f.count}×</em></div>`;
  }).join('');
}

async function startCamera(deviceId) {
  try {
    await scanner.start(deviceId);
    $('camera-msg').hidden = true;
    const devices = (await navigator.mediaDevices.enumerateDevices()).filter(d => d.kind === 'videoinput');
    const active = scanner.stream.getVideoTracks()[0].getSettings().deviceId;
    $('device').innerHTML = devices.map((d, i) =>
      `<option value="${d.deviceId}" ${d.deviceId === active ? 'selected' : ''}>${d.label || 'Camera ' + (i + 1)}</option>`).join('');
  } catch (e) {
    $('camera-msg').hidden = false;
    $('camera-msg').textContent = `Couldn't open the camera (${e.name}). You can still fill in the cube by hand below.`;
  }
}

// ---------- net editor ----------

const NET_POS = { U: [0, 3], L: [3, 0], F: [3, 3], R: [3, 6], B: [3, 9], D: [6, 3] };

function renderNet() {
  const cells = [];
  for (const f of FACES) {
    const [r0, c0] = NET_POS[f];
    for (let k = 0; k < 9; k++) {
      const i = FACES.indexOf(f) * 9 + k, v = facelet(i), centre = k === 4;
      cells.push(`<button class="sticker ${centre ? 'centre' : ''} ${v ? '' : 'empty'} ${state.overrides[i] ? 'edited' : ''} ${state.fixed.has(i) ? (state.uncertain ? 'fixed uncertain' : 'fixed') : ''}"
        data-i="${i}" style="grid-row:${r0 + Math.floor(k / 3) + 1};grid-column:${c0 + k % 3 + 1};${v ? `background:${hex(v)}` : ''}"
        title="${FACE_NAMES[f]} face${centre ? ' centre' : ''}" ${centre ? 'disabled' : ''}>${centre ? f : ''}</button>`);
    }
  }
  $('net').innerHTML = cells.join('');
  $('palette').innerHTML = FACES.split('').map(f => `<button class="swatch ${state.paint === f ? 'active' : ''}"
      data-face="${f}" style="background:${hex(f)}" title="${colourName(f)} (${FACE_NAMES[f]} centre)"></button>`).join('');

  const fl = facelets();
  const missing = fl.filter(v => !v).length;
  let msg = null;
  if (missing) msg = `${missing} sticker${missing > 1 ? 's' : ''} still unknown — scan the remaining faces or paint them.`;
  else msg = validate(fl.join(''), colourName);
  $('validation').textContent = msg ?? 'Looks like a valid cube. Ready to solve!';
  $('validation').className = msg ? 'warn' : 'ok';
  const n = state.fixed.size;
  $('layout-note').innerHTML = [
    state.layoutNote,
    n && !msg ? (state.uncertain
      ? `<b>${n} stickers looked misread and were corrected (dashed outline), but this was a close call</b> — compare them with your cube.`
      : `${n} stickers looked misread and were corrected (dashed outline) — compare them with your cube.`) : '',
  ].filter(Boolean).join(' ');
  $('find-layout').hidden = !msg || Object.keys(state.scans).length < 6;
  $('solve').disabled = !!msg || !solver.ready;
}

function fillByHand() {
  for (const f of FACES) if (!known(f)) state.manual[f] = true;
  recompute();
}

function resetAll() {
  Object.assign(state, { scans: {}, manual: {}, auto: {}, overrides: {}, current: 'F', names: nameFaces({}),
    fixed: new Set(), uncertain: false, layoutNote: '' });
  autoScan.reset();
  renderAll();
}

// ---------- solving & playback ----------

const MOVE_TEXT = { '': 'clockwise', "'": 'anticlockwise', '2': 'half turn (180°)' };

function describe(m) {
  const f = m[0];
  return `Turn the <b>${FACE_NAMES[f]}</b> face (<b style="color:${hex(f)}">${colourName(f)}</b> centre) ` +
    `${MOVE_TEXT[m.slice(1)]}${m.endsWith('2') ? '' : ', as seen looking straight at that face'}.`;
}

function colours() { return Object.fromEntries(FACES.split('').map(f => [f, hex(f)])); }

function solve() {
  const s = facelets().join('');
  $('solve').disabled = true;
  $('solve').textContent = 'Solving…';
  setTimeout(() => {
    const result = window.Cube.fromString(s).solve().trim();
    $('solve').textContent = 'Solve';
    solver.scrambled = s;
    solver.moves = result ? result.split(/\s+/) : [];
    solver.index = 0;
    solver.playing = false;
    viewer.setCube(s, colours());
    viewer.resetView();
    $('solution').hidden = false;
    $('hold').innerHTML = `Hold your cube with <b style="color:${hex('F')}">${colourName('F')}</b> facing you and ` +
      `<b style="color:${hex('U')}">${colourName('U')}</b> on top, then follow along.`;
    renderMoves();
    renderNet();
    $('solution').scrollIntoView({ behavior: 'smooth' });
  }, 30);
}

function renderMoves() {
  const n = solver.moves.length;
  $('moves').innerHTML = solver.moves.map((m, i) =>
    `<button class="move ${i < solver.index ? 'done' : ''} ${i === solver.index ? 'next' : ''}" data-i="${i}">${m}</button>`).join('');
  $('progress').textContent = n ? `Move ${Math.min(solver.index + 1, n)} of ${n}` : 'Already solved!';
  if (!n) $('current').innerHTML = 'Nothing to do — the cube is solved.';
  else if (solver.index >= n) $('current').innerHTML = '🎉 Solved!';
  else $('current').innerHTML = `<span class="big">${solver.moves[solver.index]}</span> ${describe(solver.moves[solver.index])}`;
  $('play').textContent = solver.playing ? '⏸ Pause' : '▶ Play';
}

const duration = () => 900 / Number($('speed').value);

async function step(dir) {
  if (solver.busy) return;
  if (dir > 0 && solver.index >= solver.moves.length) return;
  if (dir < 0 && solver.index <= 0) return;
  solver.busy = true;
  if (dir > 0) { await viewer.model.move(solver.moves[solver.index], duration()); solver.index++; }
  else { solver.index--; await viewer.model.move(invertMove(solver.moves[solver.index]), duration()); }
  solver.busy = false;
  renderMoves();
}

async function play() {
  if (solver.playing) { solver.playing = false; renderMoves(); return; }
  if (solver.index >= solver.moves.length) jumpTo(0);
  solver.playing = true;
  renderMoves();
  while (solver.playing && solver.index < solver.moves.length) {
    await step(1);
    await new Promise(r => setTimeout(r, duration() * 0.35));
  }
  solver.playing = false;
  renderMoves();
}

function jumpTo(i) {
  if (solver.busy) return;
  solver.playing = false;
  viewer.setCube(solver.scrambled, colours());
  for (let k = 0; k < i; k++) viewer.model.move(solver.moves[k]);
  solver.index = i;
  renderMoves();
}

// ---------- wiring ----------

function renderAll() { updateScanUI(); renderNet(); }

$('capture').onclick = capture;
$('mode').onclick = e => {
  const m = e.target.dataset.mode;
  if (!m || m === state.mode) return;
  state.mode = m;
  resetAll();
};
$('mirror').onchange = e => { scanner.mirror = e.target.checked; updateScanUI(); };
$('device').onchange = e => startCamera(e.target.value);
$('chips').onclick = e => { const f = e.target.dataset.face; if (f) { state.current = f; updateScanUI(); } };
$('palette').onclick = e => { const f = e.target.dataset.face; if (f) { state.paint = f; renderNet(); } };
$('net').onclick = e => {
  const i = e.target.dataset.i;
  if (i === undefined || Number(i) % 9 === 4) return;
  state.overrides[i] = state.paint;
  state.fixed.delete(Number(i));
  renderNet();
};
$('by-hand').onclick = fillByHand;
$('find-layout').onclick = () => { state.fixed.clear(); findLayout(); };
$('reset').onclick = resetAll;
$('solve').onclick = solve;
$('play').onclick = play;
$('next').onclick = () => { solver.playing = false; step(1); };
$('prev').onclick = () => { solver.playing = false; step(-1); };
$('first').onclick = () => jumpTo(0);
$('last').onclick = () => jumpTo(solver.moves.length);
$('moves').onclick = e => { const i = e.target.dataset.i; if (i !== undefined) jumpTo(Number(i)); };
$('view-reset').onclick = () => viewer.resetView();

document.addEventListener('keydown', e => {
  if (e.target.tagName === 'SELECT' || e.target.tagName === 'INPUT') return;
  if (e.code === 'Space' && $('solution').hidden) { e.preventDefault(); capture(); }
  else if (!$('solution').hidden && e.code === 'ArrowRight') { solver.playing = false; step(1); }
  else if (!$('solution').hidden && e.code === 'ArrowLeft') { solver.playing = false; step(-1); }
  else if (!$('solution').hidden && e.code === 'Space') { e.preventDefault(); play(); }
});

renderAll();
startCamera();
// Building the solver's lookup tables takes about a second; do it after first paint.
setTimeout(() => {
  window.Cube.initSolver();
  solver.ready = true;
  $('solver-status').hidden = true;
  renderNet();
}, 50);

// Handy for debugging from the browser console.
window.cubeApp = { state, scanner, solver, viewer, autoScan };
