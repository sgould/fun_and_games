// 3D cube made of 26 cubies. Coordinates: +x = Right, +y = Up, +z = Front.
// Facelet strings use Kociemba order U R F D L B, nine stickers per face, row-major,
// each face viewed from outside (U with B at the top, D with F at the top,
// the four side faces with U at the top).
import * as THREE from '../vendor/three.module.js';

export const FACES = 'URFDLB';

const NORMALS = {
  U: new THREE.Vector3(0, 1, 0),
  R: new THREE.Vector3(1, 0, 0),
  F: new THREE.Vector3(0, 0, 1),
  D: new THREE.Vector3(0, -1, 0),
  L: new THREE.Vector3(-1, 0, 0),
  B: new THREE.Vector3(0, 0, -1),
};

// Clockwise quarter turn of each face, as seen looking at that face.
const MOVES = {
  U: { axis: 'y', layer: 1, sign: -1 },
  D: { axis: 'y', layer: -1, sign: 1 },
  R: { axis: 'x', layer: 1, sign: -1 },
  L: { axis: 'x', layer: -1, sign: 1 },
  F: { axis: 'z', layer: 1, sign: -1 },
  B: { axis: 'z', layer: -1, sign: 1 },
};

export function faceletIndex(face, x, y, z) {
  let row, col;
  switch (face) {
    case 'U': row = z + 1; col = x + 1; break;
    case 'D': row = 1 - z; col = x + 1; break;
    case 'F': row = 1 - y; col = x + 1; break;
    case 'B': row = 1 - y; col = 1 - x; break;
    case 'R': row = 1 - y; col = 1 - z; break;
    case 'L': row = 1 - y; col = z + 1; break;
  }
  return FACES.indexOf(face) * 9 + row * 3 + col;
}

function faceFromNormal(n) {
  for (const f of FACES) if (NORMALS[f].dot(n) > 0.9) return f;
  throw new Error('bad normal');
}

export function parseMove(m) {
  const mod = m.slice(1);
  return { face: m[0], turns: mod === '2' ? 2 : mod === "'" ? -1 : 1 };
}

export function invertMove(m) {
  if (m.endsWith('2')) return m;
  return m.endsWith("'") ? m[0] : m + "'";
}

function roundedRect(size, radius) {
  const h = size / 2, s = new THREE.Shape();
  s.moveTo(-h + radius, -h);
  s.lineTo(h - radius, -h); s.quadraticCurveTo(h, -h, h, -h + radius);
  s.lineTo(h, h - radius); s.quadraticCurveTo(h, h, h - radius, h);
  s.lineTo(-h + radius, h); s.quadraticCurveTo(-h, h, -h, h - radius);
  s.lineTo(-h, -h + radius); s.quadraticCurveTo(-h, -h, -h + radius, -h);
  return new THREE.ShapeGeometry(s, 4);
}

export class CubeModel {
  constructor(facelets, colors = {}) {
    this.root = new THREE.Group();
    this.cubies = [];
    this.materials = {};
    for (const f of FACES) {
      this.materials[f] = new THREE.MeshStandardMaterial({ color: colors[f] ?? 0x888888, roughness: 0.4 });
    }
    const bodyGeo = new THREE.BoxGeometry(0.98, 0.98, 0.98);
    const bodyMat = new THREE.MeshStandardMaterial({ color: 0x111111, roughness: 0.6 });
    const stickerGeo = roundedRect(0.84, 0.12);
    const zAxis = new THREE.Vector3(0, 0, 1);

    for (let x = -1; x <= 1; x++) for (let y = -1; y <= 1; y++) for (let z = -1; z <= 1; z++) {
      if (!x && !y && !z) continue;
      const cubie = new THREE.Group();
      cubie.position.set(x, y, z);
      cubie.add(new THREE.Mesh(bodyGeo, bodyMat));
      for (const f of FACES) {
        const n = NORMALS[f];
        if (n.x * x + n.y * y + n.z * z !== 1) continue;
        const letter = facelets[faceletIndex(f, x, y, z)];
        const sticker = new THREE.Mesh(stickerGeo, this.materials[letter]);
        sticker.position.copy(n).multiplyScalar(0.492);
        sticker.quaternion.setFromUnitVectors(zAxis, n);
        sticker.userData = { letter, normal: n.clone() };
        cubie.add(sticker);
      }
      this.root.add(cubie);
      this.cubies.push(cubie);
    }
  }

  readFacelets() {
    const out = Array(54);
    for (const c of this.cubies) {
      const { x, y, z } = c.position;
      for (const s of c.children) {
        if (!s.userData.normal) continue;
        const face = faceFromNormal(s.userData.normal.clone().applyQuaternion(c.quaternion));
        out[faceletIndex(face, Math.round(x), Math.round(y), Math.round(z))] = s.userData.letter;
      }
    }
    return out.join('');
  }

  // Turn one face. duration in ms; 0 applies the move instantly.
  move(m, duration = 0) {
    const { face, turns } = parseMove(m);
    const spec = MOVES[face];
    const angle = spec.sign * turns * Math.PI / 2;
    const axis = new THREE.Vector3();
    axis[spec.axis] = 1;
    const layer = this.cubies.filter(c => Math.round(c.position[spec.axis]) === spec.layer);
    const pivot = new THREE.Group();
    this.root.add(pivot);
    layer.forEach(c => pivot.attach(c));

    const finish = () => {
      pivot.quaternion.setFromAxisAngle(axis, angle);
      layer.forEach(c => { this.root.attach(c); snap(c); });
      this.root.remove(pivot);
    };
    if (!duration) { finish(); return Promise.resolve(); }
    if (turns === 2) duration *= 1.5;

    return new Promise(resolve => {
      const t0 = performance.now();
      const step = now => {
        const t = Math.min(1, (now - t0) / duration);
        const e = t < 0.5 ? 2 * t * t : 1 - (-2 * t + 2) ** 2 / 2;
        pivot.quaternion.setFromAxisAngle(axis, angle * e);
        if (t < 1) requestAnimationFrame(step);
        else { finish(); resolve(); }
      };
      requestAnimationFrame(step);
    });
  }
}

// Remove floating-point drift so cubies stay on the integer lattice.
function snap(c) {
  c.position.set(Math.round(c.position.x), Math.round(c.position.y), Math.round(c.position.z));
  const m = new THREE.Matrix4().makeRotationFromQuaternion(c.quaternion);
  m.elements = m.elements.map(Math.round);
  c.quaternion.setFromRotationMatrix(m);
}
