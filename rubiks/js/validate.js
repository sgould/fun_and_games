// Checks that a 54-letter facelet string describes a cube that can actually be
// solved, and explains what is wrong when it can't (usually a misread sticker).

const CORNER_FACELETS = [[8, 9, 20], [6, 18, 38], [0, 36, 47], [2, 45, 11],
  [29, 26, 15], [27, 44, 24], [33, 53, 42], [35, 17, 51]];
const CORNER_COLORS = ['URF', 'UFL', 'ULB', 'UBR', 'DFR', 'DLF', 'DBL', 'DRB'];
const EDGE_FACELETS = [[5, 10], [7, 19], [3, 37], [1, 46], [32, 16], [28, 25],
  [30, 43], [34, 52], [23, 12], [21, 41], [50, 39], [48, 14]];
const EDGE_COLORS = ['UR', 'UF', 'UL', 'UB', 'DR', 'DF', 'DL', 'DB', 'FR', 'FL', 'BL', 'BR'];

function parity(perm) {
  let p = 0;
  for (let i = 0; i < perm.length; i++)
    for (let j = i + 1; j < perm.length; j++) if (perm[i] > perm[j]) p ^= 1;
  return p;
}

// name: face letter -> human colour name, used in messages.
export function validate(facelets, name = f => f) {
  const counts = {};
  for (const c of facelets) counts[c] = (counts[c] || 0) + 1;
  const wrong = 'URFDLB'.split('').filter(f => counts[f] !== 9);
  if (wrong.length) {
    return 'Each colour must appear 9 times: ' +
      wrong.map(f => `${name(f)} ${counts[f] || 0}`).join(', ') + '.';
  }

  const cp = [], co = [];
  for (let i = 0; i < 8; i++) {
    const cols = CORNER_FACELETS[i].map(k => facelets[k]);
    const ori = cols.findIndex(c => c === 'U' || c === 'D');
    const j = ori < 0 ? -1 : CORNER_COLORS.findIndex(cc =>
      cc[0] === cols[ori] && cc[1] === cols[(ori + 1) % 3] && cc[2] === cols[(ori + 2) % 3]);
    if (j < 0) return `A corner shows ${cols.map(name).join('/')}, which isn't a real corner piece.`;
    cp.push(j); co.push(ori);
  }
  const ep = [], eo = [];
  for (let i = 0; i < 12; i++) {
    const [a, b] = EDGE_FACELETS[i].map(k => facelets[k]);
    let j = EDGE_COLORS.indexOf(a + b), flip = 0;
    if (j < 0) { j = EDGE_COLORS.indexOf(b + a); flip = 1; }
    if (j < 0) return `An edge shows ${name(a)}/${name(b)}, which isn't a real edge piece.`;
    ep.push(j); eo.push(flip);
  }
  if (new Set(cp).size !== 8) return 'The same corner piece appears twice — a sticker was misread.';
  if (new Set(ep).size !== 12) return 'The same edge piece appears twice — a sticker was misread.';
  if (co.reduce((s, v) => s + v, 0) % 3) return 'One corner appears twisted — check the corner stickers.';
  if (eo.reduce((s, v) => s + v, 0) % 2) return 'One edge appears flipped — check the edge stickers.';
  if (parity(cp) !== parity(ep)) return 'Two pieces appear swapped — check the stickers carefully.';
  return null;
}
