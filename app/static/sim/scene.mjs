import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { createRoad, roadHeight, previewWorldLength, METERS_PER_WORLD_UNIT } from './geometry.mjs';

// Illustration scale: see METERS_PER_WORLD_UNIT in geometry.mjs, which owns the
// value and the reason for it. It was 90 and is now 35, chosen so a cruise and
// a hard pull look different; the ~132-unit loop is therefore about 4.6 km.
// Elevation is decorative, never a grade or thermal-model input.
export { METERS_PER_WORLD_UNIT } from './geometry.mjs';
const TAU = Math.PI * 2;
const UP = new THREE.Vector3(0, 1, 0);

// ---------------------------------------------------------------- palette
// Every colour in this file lives here, keyed by MEANING rather than by the
// mesh that happens to use it, so a theme is one table and not 43 edits. A
// theme change re-tints these same material instances: no geometry is rebuilt,
// nothing is disposed, and the car, camera, follow state and preview ribbon are
// untouched by it.
//
// An entry is a colour, or an object carrying the extra channels that colour
// owns ({ color, emissive, emissiveIntensity, opacity }). Both themes must
// define any optional channel they use, because a switch resets what it does
// not set: emissive falls back to black, and opacity is left alone.
//
// The keys marked NIGHT LIGHT are read by paint.glow() instead of paint.mat(),
// and for those `opacity: 0` means the light is OFF: the flat tinter hides the
// material outright. That is the whole light/dark switch for the lit scene --
// no geometry appears or disappears, and nothing of the night can leak into
// daylight, because one table decides it.
//
// `lighting` is not a colour but belongs with them: a dark scene needs a dimmer
// ambient and a cooler key, and the tone-mapping exposure moves with them.
const PALETTES = {
  light: {
    // stage
    clear: 0xeff0e6,
    sky: 0xfffaf0,
    bounce: 0x8a9b89,
    keyLight: 0xfff6e8,
    lighting: { hemi: 2.9, key: 3.5, exposure: 1.25 },
    // terrain
    ground: 0xb9c9aa,
    bank: 0xc5bba6,
    floor: 0xe8ebdf,
    // road
    verge: 0xa3ac91,
    road: 0x505952,
    roadLine: 0xf3eacb,
    post: 0xeee8d7,
    reflector: 0xb8b176,
    lampPool: { color: 0xffe7b4, opacity: 0 },   // NIGHT LIGHT -- off by day
    // landscape
    bark: 0x8d8266,
    leafDark: 0x708c6d,
    leafMid: 0x8aa37c,
    leafLight: 0x9aad84,
    stone: 0xc9ceba,
    stationDeck: 0xd5d6c3,
    stationWall: 0xeee9d9,
    stationRoof: 0x81988c,
    stationGlass: 0x758b83,
    stationMullion: 0xe5dfce,
    stationPanel: 0x4d665f,
    windowLit: { color: 0xffd7a0, opacity: 0 },  // NIGHT LIGHT -- off by day
    pad: 0xd7d9c8,
    monument: 0xc2b378,
    // car
    carBody: 0xf6f1dc,
    carGlass: 0x334b47,
    carTrim: 0x303c36,
    carAlloy: 0xb8bcae,
    carAccent: 0x78886d,
    headlight: { color: 0xfbf5d6, emissive: 0xfbf0ca, emissiveIntensity: 0.4 },
    taillight: { color: 0xa65845, emissive: 0x8d3f31, emissiveIntensity: 0.2 },
    // NIGHT LIGHT -- all three off by day, so the daylight car keeps exactly
    // the subtle emissive highlight it has always had and nothing more.
    headlightBeam: { color: 0xfff0c8, opacity: 0 },
    headlightPool: { color: 0xffeec4, opacity: 0 },
    taillightGlow: { color: 0xff4a2c, opacity: 0 },
    // the preview horizon band
    preview: { color: 0xd6c775, emissive: 0x8e883f, emissiveIntensity: 0.3, opacity: 0.6 },
    // engine inset
    blockMetal: 0xc5cbbe,
    engineDark: 0x53625a,
    // the temperature ramp -- see temperatureColor()
    tempUnknown: 0x9aa59e,
    tempCool: 0x789e95,
    tempWarm: 0xd4b86a,
    tempHot: 0xbd6551,
  },
  dark: {
    clear: 0x1a2220,
    sky: 0x6a86a4,
    bounce: 0x22322a,
    keyLight: 0xbcd0ff,
    // Night, not a blackout. The first pass sat at hemi 1.15 / key 1.5 and the
    // lamp pools read well while the ground, the trees and the road between
    // them disappeared -- the scene lost its shape, which is the one thing an
    // isometric view is for. Raised on 21 September after looking at it: still
    // clearly below the light theme's 2.9 / 3.5, so a lamp is still the
    // brightest thing on the verge, but the landscape is legible again.
    // Raise `hemi` first if it is still too dark; it lifts the fill without
    // touching the lamps' contrast.
    lighting: { hemi: 1.95, key: 2.3, exposure: 1.15 },
    ground: 0x4a6351,
    bank: 0x4f483c,
    floor: 0x28302b,
    verge: 0x45503e,
    road: 0x333d3e,
    // Markings, posts and reflectors stay bright on purpose: they are the
    // legibility of the road at night, and the ribbon below needs a road to
    // read against.
    roadLine: 0xe9dfae,
    post: 0x8c8878,
    // The reflector cube IS the lamp head after dark -- the same mesh, driven
    // hard enough to be the brightest thing on the verge. No geometry is added
    // for it, which is why the daylight post is untouched.
    reflector: { color: 0xf8e7a6, emissive: 0xffd169, emissiveIntensity: 2.4 },
    lampPool: { color: 0xffd694, opacity: 0.4 },
    bark: 0x4a4038,
    leafDark: 0x33503e,
    leafMid: 0x406048,
    leafLight: 0x4c6e54,
    stone: 0x636a5e,
    stationDeck: 0x525a50,
    stationWall: 0x6e7366,
    stationRoof: 0x455750,
    stationGlass: { color: 0x86a89b, emissive: 0x27453a, emissiveIntensity: 0.55 },
    stationMullion: 0x8a8676,
    stationPanel: 0x3a4d46,
    // One material for every lit pane; which bays are lit and how brightly is
    // a grey vertex colour per bay, so "inhabited" costs nothing extra.
    windowLit: { color: 0xffc981, opacity: 0.88 },
    pad: 0x51574c,
    monument: 0xa8944f,
    // The car stays the brightest object in either theme; it is what the eye
    // follows.
    carBody: 0xe3dcc2,
    carGlass: 0x22343a,
    carTrim: 0x272e2a,
    carAlloy: 0xa0a699,
    carAccent: 0x5c6b52,
    headlight: { color: 0xfffce8, emissive: 0xfff3c4, emissiveIntensity: 2.6 },
    taillight: { color: 0xd8503c, emissive: 0xf03418, emissiveIntensity: 2.2 },
    // The beams are read against a dark road, so they are faint on purpose:
    // the pool is what says "the headlights are on", the cones only say where
    // they point. Raising these is the first thing to try if the night reads
    // flat, and the first thing to lower if it reads like a game.
    headlightBeam: { color: 0xfff0c8, opacity: 0.24 },
    headlightPool: { color: 0xffeec4, opacity: 0.5 },
    taillightGlow: { color: 0xff4a2c, opacity: 0.3 },
    // Brighter, more opaque and more emissive than the light theme, because it
    // is read against a dark ground rather than a pale one.
    preview: { color: 0xe8e587, emissive: 0xb6b74e, emissiveIntensity: 0.95, opacity: 0.72 },
    blockMetal: 0x7e857c,
    engineDark: 0x2c3733,
    tempUnknown: 0x5d6763,
    tempCool: 0x54b5a4,
    tempWarm: 0xebc369,
    tempHot: 0xe06a52,
  },
};
const themeName = name => (Object.prototype.hasOwnProperty.call(PALETTES, name) ? name : 'light');
function entry(theme, key) {
  const spec = PALETTES[theme][key];
  if (spec === undefined) throw new Error(`scene palette has no key "${key}"`);
  return typeof spec === 'number' ? { color: spec } : spec;
}
function tint(material, theme, key) {
  const spec = entry(theme, key);
  material.color.set(spec.color);
  material.emissive.set(spec.emissive ?? 0x000000);
  material.emissiveIntensity = spec.emissiveIntensity ?? 1;
  if (spec.opacity !== undefined) material.opacity = spec.opacity;
  return material;
}
// The tinter for an UNLIT material: a lamp glow is not shaded by the scene, it
// IS the light, so it carries no emissive channel and no normals. Opacity is
// the whole switch -- a theme that gives it 0 turns the light off, and the
// material is hidden outright rather than drawn as a transparent nothing.
function tintFlat(material, theme, key) {
  const spec = entry(theme, key);
  material.color.set(spec.color);
  material.opacity = spec.opacity ?? 1;
  material.visible = material.opacity > 0;
  return material;
}
// Materials are built through a painter so that a later setTheme() re-tints the
// instances already in the graph. `loose` is for a material whose colour is
// data, not decoration -- the engine nodes carry a temperature, and their owner
// repaints them.
// `glow` is `mat` for light itself: an additive, unlit, vertex-coloured
// material whose geometry carries the falloff. It is tracked and re-tinted by
// the same apply(), so one setTheme() call switches the whole night on or off.
function createPainter() {
  const tracked = [];
  let active = 'light';
  const build = (key, extra) => tint(new THREE.MeshStandardMaterial({ roughness: 0.82, ...extra }), active, key);
  const buildFlat = (key, extra) => tintFlat(new THREE.MeshBasicMaterial({
    transparent: true, depthWrite: false, vertexColors: true,
    blending: THREE.AdditiveBlending, side: THREE.DoubleSide, ...extra,
  }), active, key);
  return {
    theme: () => active,
    mat(key, extra = {}) { const material = build(key, extra); tracked.push([material, key, tint]); return material; },
    loose(key, extra = {}) { return build(key, extra); },
    glow(key, extra = {}) { const material = buildFlat(key, extra); tracked.push([material, key, tintFlat]); return material; },
    apply(name) { active = themeName(name); tracked.forEach(([material, key, paint]) => paint(material, active, key)); },
  };
}

function mesh(parent, geometry, material, position = [0, 0, 0]) {
  const item = new THREE.Mesh(geometry, material);
  item.position.set(...position);
  item.castShadow = true;
  item.receiveShadow = true;
  parent.add(item);
  return item;
}
function box(parent, size, material, position) {
  return mesh(parent, new THREE.BoxGeometry(...size), material, position);
}
function pipe(parent, points, radius, material) {
  const curve = new THREE.CatmullRomCurve3(points.map(p => new THREE.Vector3(...p)), false, 'centripetal');
  return mesh(parent, new THREE.TubeGeometry(curve, 32, radius, 7, false), material);
}

// ------------------------------------------------------------ night light
// NOTHING BELOW IS A THREE.LIGHT. There is one lamp every few world units and
// a real light is per-fragment, so the scene adds zero of them: a lamp reads
// as a lamp because it is BRIGHTER than what surrounds it, which an emissive
// surface plus an additive patch says for the cost of a draw call.
//
// Grey vertex colours carry the FALLOFF only -- the same division of labour
// the terrain already uses for its patch variation. The light's colour is the
// themed material, so daylight re-tints and hides these without touching a
// vertex, and no Texture is ever created (nothing for dispose to miss).
const softEdge = r => { const t = Math.max(0, 1 - Math.abs(r)); return t * t * (3 - 2 * t); };
const lightBuffer = () => ({ positions: [], colors: [], indices: [] });
// One quad grid appended into a shared buffer: every lamp pool on the loop,
// every lit window and both beams are built this way, so each family of lights
// ends up as ONE geometry and ONE draw call however many of them there are.
function addQuadGrid(target, along, across, place, shade) {
  const base = target.positions.length / 3;
  for (let i = 0; i <= along; i++) {
    const s = i / along;
    for (let j = 0; j <= across; j++) {
      const v = j / across;
      target.positions.push(...place(s, v));
      const k = shade(s, v);
      target.colors.push(k, k, k);
      if (i < along && j < across) {
        const a = base + i * (across + 1) + j;
        const b = a + across + 1;
        target.indices.push(a, a + 1, b, b, a + 1, b + 1);
      }
    }
  }
  return target;
}
function lightGeometry({ positions, colors, indices }) {
  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3));
  geometry.setAttribute('color', new THREE.Float32BufferAttribute(colors, 3));
  geometry.setIndex(indices);
  return geometry;
}
// Above the road and its markings (0.07) and below the preview ribbon (0.085),
// so lamplight brightens the paint instead of being punched through by it, and
// the yellow-green horizon band still composites on top of every lit surface.
const LIGHT_LIFT = 0.075;
// A pool of light lying ON the road: it samples the road itself, so it follows
// the bend and the hill exactly and cannot float or sink on a slope. Offsets
// and widths are in the same across-road units ribbonGeometry uses.
function addRoadPool(target, road, centre, length, width, offset) {
  addQuadGrid(target, 10, 4, (s, v) => {
    const { position: p, tangent: t } = road.atDistance(centre + (s - 0.5) * length);
    const norm = Math.hypot(t[0], t[2]);
    const w = offset + (v - 0.5) * width;
    return [p[0] - t[2] / norm * w, p[1] + LIGHT_LIFT, p[2] + t[0] / norm * w];
  }, (s, v) => softEdge((s - 0.5) * 2) * softEdge((v - 0.5) * 2));
}
// A flat spill in a LOCAL frame, for light carried by something that moves:
// +X is forward, it widens with distance, and it fades to nothing at both
// ends. The far end going dark is what keeps it honest -- a straight beam on a
// bending, climbing road would otherwise drift off the surface where it is
// still bright.
function addLocalSpill(target, near, far, halfNear, halfFar, y, lead = 0.18) {
  addQuadGrid(target, 8, 5,
    (s, v) => [near + (far - near) * s, y, (v - 0.5) * 2 * (halfNear + (halfFar - halfNear) * s)],
    (s, v) => Math.min(1, s / lead) * softEdge((s - lead) / (1 - lead)) * softEdge((v - 0.5) * 2));
}
// The visible cone of a headlight: lateral surface only, along +X, brightest
// at the lens. The falloff is quadratic because the cross-section it is spread
// over grows with the square of the distance.
function beamGeometry(length, near, far) {
  return lightGeometry(addQuadGrid(lightBuffer(), 4, 14, (s, v) => {
    const angle = v * TAU;
    const radius = near + (far - near) * s;
    return [length * s, Math.sin(angle) * radius, Math.cos(angle) * radius];
  }, s => (1 - s) * (1 - s)));
}
// Light casts no shadow and receives none, and it draws before the preview
// ribbon so the ribbon stays the thing on top of the road.
function glowMesh(parent, geometry, material, position = [0, 0, 0]) {
  const item = new THREE.Mesh(geometry, material);
  item.position.set(...position);
  item.castShadow = false;
  item.receiveShadow = false;
  item.renderOrder = -1;
  parent.add(item);
  return item;
}

function disposeGraph(scene) {
  const geometries = new Set();
  const materials = new Set();
  scene.traverse(item => {
    if (item.geometry) geometries.add(item.geometry);
    if (item.material) (Array.isArray(item.material) ? item.material : [item.material]).forEach(m => materials.add(m));
    if (item.shadow?.map) item.shadow.map.dispose();
  });
  geometries.forEach(g => g.dispose());
  materials.forEach(m => m.dispose());
}
function stage(host, { extent, position, target, shadows = true }) {
  const paint = createPainter();
  const scene = new THREE.Scene();
  const camera = new THREE.OrthographicCamera(-extent, extent, extent, -extent, 0.1, 250);
  camera.position.set(...position);
  camera.lookAt(...target);
  const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true, powerPreference: 'low-power' });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
  // The canvas stays transparent in BOTH themes (clear alpha 0), so the page's
  // own themed panel is the background and the engine inset keeps blending into
  // the card it sits in. The clear colour is themed all the same.
  renderer.setClearColor(PALETTES.light.clear, 0);
  scene.background = null;
  renderer.shadowMap.enabled = shadows;
  renderer.shadowMap.type = THREE.PCFSoftShadowMap;
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = PALETTES.light.lighting.exposure;
  renderer.domElement.style.cssText = 'display:block;width:100%;height:100%;touch-action:none';
  renderer.domElement.setAttribute('aria-hidden', 'true');
  host.appendChild(renderer.domElement);
  const hemi = new THREE.HemisphereLight(PALETTES.light.sky, PALETTES.light.bounce, PALETTES.light.lighting.hemi);
  scene.add(hemi);
  const sun = new THREE.DirectionalLight(PALETTES.light.keyLight, PALETTES.light.lighting.key);
  sun.position.set(-25, 45, 30);
  sun.castShadow = shadows;
  sun.shadow.mapSize.set(2048, 2048);
  Object.assign(sun.shadow.camera, { left: -45, right: 45, top: 40, bottom: -40, near: 1, far: 120 });
  sun.shadow.normalBias = 0.05;
  sun.shadow.bias = -0.00015;
  sun.shadow.radius = 4;
  scene.add(sun);
  let disposed = false;
  const render = () => { if (!disposed) renderer.render(scene, camera); };
  const resize = () => {
    if (disposed) return;
    const width = Math.max(1, host.clientWidth);
    const height = Math.max(1, host.clientHeight);
    const aspect = width / height;
    const halfHeight = aspect < 1.3 ? extent * 1.3 / aspect : extent;
    camera.left = -halfHeight * aspect;
    camera.right = halfHeight * aspect;
    camera.top = halfHeight;
    camera.bottom = -halfHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(width, height, false);
    render();
  };
  const observer = new ResizeObserver(resize);
  observer.observe(host);
  resize();
  // Lights, exposure and clear colour follow the palette; the camera, the
  // controls and every geometry stay exactly where they were.
  const setTheme = name => {
    if (disposed) return;
    paint.apply(name);
    const palette = PALETTES[paint.theme()];
    hemi.color.set(palette.sky);
    hemi.groundColor.set(palette.bounce);
    hemi.intensity = palette.lighting.hemi;
    sun.color.set(palette.keyLight);
    sun.intensity = palette.lighting.key;
    renderer.setClearColor(palette.clear, 0);
    renderer.toneMappingExposure = palette.lighting.exposure;
  };
  return { scene, camera, renderer, render, paint, setTheme, theme: paint.theme, dispose() {
    disposed = true;
    observer.disconnect();
    disposeGraph(scene);
    renderer.dispose();
    renderer.domElement.remove();
  } };
}

function terrain(scene, paint) {
  const vertices = [];
  const colors = [];
  const indices = [];
  const rings = 10;
  const sectors = 80;
  for (let ring = 0; ring <= rings; ring++) {
    const radius = ring / rings;
    for (let i = 0; i <= sectors; i++) {
      const angle = i / sectors * TAU;
      const irregular = 1 + 0.025 * Math.sin(3 * angle) + 0.016 * Math.cos(7 * angle);
      const x = Math.sin(angle) * 34 * radius * irregular;
      const z = Math.cos(angle) * 25 * radius * irregular;
      const roadRadius = Math.hypot(x / 25, z / 16);
      const u = Math.atan2(x / 25, z / 16) / TAU;
      const hill = roadHeight(u) - 0.24;
      const y = 0.12 + hill * Math.min(1, Math.max(0, (roadRadius - 0.1) / 0.7));
      vertices.push(x, y, z);
      // Vertex colour carries the patch-to-patch VARIATION only, as a grey
      // multiplier; the ground colour itself is the themed material, so the
      // terrain re-tints without rewriting the attribute.
      const shade = 0.98 + 0.025 * Math.sin(i * 2.7 + ring);
      colors.push(shade, shade, shade);
      if (ring < rings && i < sectors) {
        const a = ring * (sectors + 1) + i;
        const b = a + sectors + 1;
        indices.push(a, a + 1, b, b, a + 1, b + 1);
      }
    }
  }
  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute('position', new THREE.Float32BufferAttribute(vertices, 3));
  geometry.setAttribute('color', new THREE.Float32BufferAttribute(colors, 3));
  geometry.setIndex(indices);
  geometry.computeVertexNormals();
  mesh(scene, geometry, paint.mat('ground', { vertexColors: true, side: THREE.DoubleSide, flatShading: true }));
  const bankVertices = [];
  const bankIndices = [];
  for (let i = 0; i <= sectors; i++) {
    const offset = (rings * (sectors + 1) + i) * 3;
    const [x, y, z] = vertices.slice(offset, offset + 3);
    bankVertices.push(x, y, z, x * 0.985, -2.2, z * 0.985);
    if (i < sectors) { const a = i * 2; bankIndices.push(a, a + 1, a + 2, a + 1, a + 3, a + 2); }
  }
  const bank = new THREE.BufferGeometry();
  bank.setAttribute('position', new THREE.Float32BufferAttribute(bankVertices, 3));
  bank.setIndex(bankIndices);
  bank.computeVertexNormals();
  mesh(scene, bank, paint.mat('bank', { side: THREE.DoubleSide, flatShading: true }));
  const floor = mesh(scene, new THREE.PlaneGeometry(300, 300), paint.mat('floor'), [0, -2.27, 0]);
  floor.rotation.x = -Math.PI / 2;
  floor.castShadow = false;
}

function ribbonGeometry(road, start, length, width, offset = 0, lift = 0.04, segments = 300) {
  const positions = new Float32Array((segments + 1) * 6);
  const indices = [];
  for (let i = 0; i <= segments; i++) {
    const { position: p, tangent: t } = road.atDistance(start + length * i / segments);
    const norm = Math.hypot(t[0], t[2]);
    const nx = -t[2] / norm;
    const nz = t[0] / norm;
    for (let side = 0; side < 2; side++) {
      const w = offset + (side - 0.5) * width;
      positions.set([p[0] + nx * w, p[1] + lift, p[2] + nz * w], i * 6 + side * 3);
    }
    if (i < segments) { const a = i * 2; indices.push(a, a + 2, a + 1, a + 1, a + 2, a + 3); }
  }
  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
  geometry.setIndex(indices);
  geometry.computeVertexNormals();
  return geometry;
}
function roadDecor(scene, road, paint) {
  mesh(scene, ribbonGeometry(road, 0, road.length, 6.6, 0, 0), paint.mat('verge', { side: THREE.DoubleSide }));
  mesh(scene, ribbonGeometry(road, 0, road.length, 5.8), paint.mat('road', { side: THREE.DoubleSide }));
  const ivory = paint.mat('roadLine', { side: THREE.DoubleSide });
  for (const offset of [-2.56, 2.56]) mesh(scene, ribbonGeometry(road, 0, road.length, 0.1, offset, 0.065), ivory);
  for (let distance = 0; distance < road.length; distance += 4.5) {
    mesh(scene, ribbonGeometry(road, distance, 1.7, 0.11, 0, 0.07, 6), ivory);
  }
  const postMat = paint.mat('post');
  // After dark this is the lamp head, not a reflector: the palette drives it
  // hard emissive and drops a pool of light on the road under it. The posts
  // sit at across-road offset -3.35, so the pool is offset the same way.
  const reflector = paint.mat('reflector');
  const pools = lightBuffer();
  for (let distance = 8; distance < road.length; distance += 9) {
    const { position: p, tangent: t } = road.atDistance(distance);
    const norm = Math.hypot(t[0], t[2]);
    const x = p[0] + t[2] / norm * 3.35;
    const z = p[2] - t[0] / norm * 3.35;
    box(scene, [0.13, 0.8, 0.13], postMat, [x, p[1] + 0.38, z]);
    box(scene, [0.16, 0.14, 0.16], reflector, [x, p[1] + 0.72, z]);
    addRoadPool(pools, road, distance, 6.4, 5.8, -1.3);
  }
  // Every pool on the loop is one geometry and one draw call, whatever the
  // loop length and post spacing above turn out to be.
  glowMesh(scene, lightGeometry(pools), paint.glow('lampPool'));
}

function landscape(scene, paint) {
  const bark = paint.mat('bark');
  const leaves = [paint.mat('leafDark'), paint.mat('leafMid'), paint.mat('leafLight')];
  const stone = paint.mat('stone', { flatShading: true });
  function ground(x, z) {
    const radius = Math.hypot(x / 25, z / 16);
    return 0.12 + (roadHeight(Math.atan2(x / 25, z / 16) / TAU) - 0.24) * Math.min(1, Math.max(0, (radius - 0.1) / 0.7));
  }
  const trees = [[-28, -5, 1.05], [-26, -10, 0.8], [-19, -18, 1.1], [-11, -21, 0.86], [0, -21, 1], [12, -20, 1.15], [23, -14, 0.9], [28, -6, 1.05], [29, 3, 0.78], [-29, 4, 0.95], [-22, 14, 0.8], [22, 13, 0.68], [-12, 6, 0.83], [-15, 2, 0.65]];
  trees.forEach(([x, z, scale], i) => {
    const tree = new THREE.Group();
    tree.position.set(x, ground(x, z), z);
    tree.scale.setScalar(scale);
    mesh(tree, new THREE.CylinderGeometry(0.16, 0.24, 2.4, 6), bark, [0, 1.2, 0]);
    const crown = mesh(tree, new THREE.IcosahedronGeometry(1.8, 0), leaves[i % leaves.length], [0, 3, 0]);
    crown.scale.set(0.92, 1.25, 0.88);
    crown.rotation.y = i * 0.7;
    scene.add(tree);
  });
  [[-16, -6], [18, 5], [12, 10], [-29, 10], [28, 8], [16, -21]].forEach(([x, z], i) => {
    const rock = mesh(scene, new THREE.DodecahedronGeometry(0.7, 0), stone, [x, ground(x, z) + 0.2, z]);
    rock.scale.set(1.4, 0.6, 0.8);
    rock.rotation.y = i;
  });
  // A compact engineering station anchors the center of the miniature.
  const station = new THREE.Group();
  station.position.set(-4.5, ground(-4.5, -2), -2);
  box(station, [10, 0.22, 7], paint.mat('stationDeck'), [0, 0.12, 0]);
  box(station, [7.4, 2.5, 4.4], paint.mat('stationWall'), [0, 1.48, 0]);
  box(station, [7.8, 0.28, 4.9], paint.mat('stationRoof'), [0, 2.85, 0]);
  box(station, [6.7, 1.3, 0.06], paint.mat('stationGlass', { metalness: 0.2, roughness: 0.4 }), [0, 1.65, 2.24]);
  const mullion = paint.mat('stationMullion');
  const bay = 1.18;
  for (let i = -2; i <= 2; i++) box(station, [0.12, 1.5, 0.12], mullion, [i * bay, 1.65, 2.3]);
  // Lit rooms: one additive quad per bay, sitting just in front of the glass
  // (2.29 against the pane at 2.24) and inside the mullion frame. WHICH bays
  // are lit and how brightly is a fixed table indexed by the bay -- never a
  // random draw, because a replay has to draw the same frame twice. One bay
  // is dark on purpose; a building with every window identical reads as a
  // texture rather than as somewhere people are.
  const rooms = [0.95, 0.34, 0.8, 0, 0.55, 1];
  const panes = lightBuffer();
  rooms.forEach((lit, i) => {
    if (lit <= 0) return;
    const centre = (i - (rooms.length - 1) / 2) * bay;
    addQuadGrid(panes, 1, 1, (s, v) => [centre + (s - 0.5) * 0.8, 1.65 + (v - 0.5) * 1.14, 2.29], () => lit);
  });
  glowMesh(station, lightGeometry(panes), paint.glow('windowLit'));
  const panel = paint.mat('stationPanel');
  box(station, [2.5, 0.12, 1.9], panel, [-1.6, 3.07, -0.4]);
  box(station, [2.5, 0.12, 1.9], panel, [1.4, 3.07, -0.4]);
  scene.add(station);
  const pad = mesh(scene, new THREE.CylinderGeometry(3.5, 3.5, 0.15, 48), paint.mat('pad'), [10, 0.21, 3]);
  pad.scale.z = 0.85;
  const monument = mesh(scene, new THREE.TorusGeometry(1.5, 0.2, 8, 32), paint.mat('monument', { metalness: 0.35 }), [10, 2, 3]);
  monument.rotation.y = -0.35;
}

// Local +X is forward. Ring sections form the coupe's hood, shoulders and roof.
function loft(parent, sections, material) {
  const vertices = [];
  for (const [x, width, bottom, top] of sections) {
    vertices.push(x, bottom, -width, x, top, -width * 0.86, x, top + 0.08, 0, x, top, width * 0.86, x, bottom, width);
  }
  const indices = [];
  for (let i = 0; i < sections.length - 1; i++) for (let j = 0; j < 5; j++) {
    const a = i * 5 + j;
    const b = i * 5 + (j + 1) % 5;
    indices.push(a, b, a + 5, b, b + 5, a + 5);
  }
  indices.push(0, 2, 1, 0, 4, 2, 2, 4, 3);
  const end = (sections.length - 1) * 5;
  indices.push(end, end + 1, end + 2, end, end + 2, end + 4, end + 2, end + 3, end + 4);
  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute('position', new THREE.Float32BufferAttribute(vertices, 3));
  geometry.setIndex(indices);
  geometry.computeVertexNormals();
  return mesh(parent, geometry, material);
}
function supra(scene, paint) {
  const car = new THREE.Group();
  const body = paint.mat('carBody', { roughness: 0.32, metalness: 0.18, side: THREE.DoubleSide });
  const glass = paint.mat('carGlass', { roughness: 0.2, metalness: 0.32, side: THREE.DoubleSide });
  const trim = paint.mat('carTrim', { roughness: 0.55 });
  const alloy = paint.mat('carAlloy', { metalness: 0.72, roughness: 0.27 });
  const accent = paint.mat('carAccent');
  loft(car, [[-3.15, 1.05, 0.57, 1.13], [-2.3, 1.37, 0.54, 1.48], [-0.7, 1.24, 0.48, 1.38], [0.8, 1.2, 0.49, 1.26], [2.25, 1.29, 0.54, 1.18], [3.25, 0.98, 0.59, 0.94]], body);
  loft(car, [[-1.98, 1.03, 1.32, 1.4], [-1.22, 0.92, 1.35, 2.01], [-0.15, 0.87, 1.3, 2.1], [0.94, 0.98, 1.26, 1.31]], glass);
  loft(car, [[-1.27, 0.94, 1.97, 2.04], [-0.19, 0.9, 2.03, 2.12]], body);
  // Long hood creases, rear haunches, splitter and a raised rear wing.
  for (const side of [-1, 1]) {
    box(car, [2, 0.05, 0.1], accent, [1.55, 1.28, side * 0.6]).rotation.z = -0.09;
    box(car, [3.9, 0.14, 0.11], trim, [-0.1, 0.52, side * 1.23]);
    box(car, [0.72, 0.17, 0.12], trim, [0.64, 1.28, side * 1.3]);
    box(car, [0.15, 0.46, 0.11], trim, [-2.65, 1.61, side * 0.8]);
    box(car, [0.26, 0.15, 0.77], paint.mat('headlight'), [2.96, 1.05, side * 0.67]);
    box(car, [0.1, 0.15, 0.77], paint.mat('taillight'), [-3.15, 1.02, side * 0.67]);
    box(car, [0.48, 0.17, 0.25], body, [0.15, 1.49, side * 1.24]);
  }
  box(car, [0.75, 0.15, 2.63], accent, [-2.64, 1.85, 0]);
  box(car, [0.22, 0.23, 1.36], trim, [3.21, 0.73, 0]);
  box(car, [0.32, 0.1, 2.3], trim, [3.14, 0.5, 0]);
  box(car, [0.12, 0.21, 1.6], trim, [-3.14, 0.64, 0]);
  const wheels = [];
  for (const x of [-2.12, 2.02]) for (const side of [-1, 1]) {
    const wheel = new THREE.Group();
    wheel.position.set(x, 0.62, side * 1.23);
    const tire = mesh(wheel, new THREE.CylinderGeometry(0.62, 0.62, 0.35, 20), trim);
    tire.rotation.x = Math.PI / 2;
    const rim = mesh(wheel, new THREE.CylinderGeometry(0.43, 0.43, 0.37, 12), alloy);
    rim.rotation.x = Math.PI / 2;
    mesh(wheel, new THREE.TorusGeometry(0.32, 0.065, 6, 12), trim, [0, 0, side * 0.2]);
    for (let spoke = 0; spoke < 5; spoke++) {
      const bar = box(wheel, [0.68, 0.055, 0.045], alloy, [0, 0, side * 0.23]);
      bar.rotation.z = spoke * Math.PI / 5;
    }
    car.add(wheel);
    wheels.push(wheel);
  }
  // Headlights, parented to the car so they follow position AND heading with
  // no per-frame work: two cones in the air saying where the light points, and
  // one spill on the road saying that it lands. The cones are tilted down but
  // never reach the ground within their length -- an additive cone welded to
  // the road would read as a wedge of plastic. Local y = 0 is where the tyres
  // touch and the car sits 0.085 above the surface, so the spills go at
  // -0.085 + LIGHT_LIFT: on the road, over its markings, under the ribbon.
  const beam = beamGeometry(4.6, 0.3, 1.15);
  const beamMaterial = paint.glow('headlightBeam');
  for (const side of [-1, 1]) {
    const cone = glowMesh(car, beam, beamMaterial, [3.06, 1.04, side * 0.67]);
    cone.scale.y = 0.52;
    cone.rotation.z = -0.055;
  }
  const ahead = lightBuffer();
  addLocalSpill(ahead, 2.6, 7.4, 0.95, 2.45, LIGHT_LIFT - 0.085);
  glowMesh(car, lightGeometry(ahead), paint.glow('headlightPool'));
  const behind = lightBuffer();
  addLocalSpill(behind, -3.3, -6.2, 0.85, 1.5, LIGHT_LIFT - 0.085, 0.25);
  glowMesh(car, lightGeometry(behind), paint.glow('taillightGlow'));
  scene.add(car);
  return { car, wheels };
}

export function createScene(host) {
  const view = stage(host, { extent: 27, position: [50, 46, 60], target: [0, 0, 0] });
  const { scene, camera, renderer, render, paint } = view;
  terrain(scene, paint);
  const road = createRoad();
  roadDecor(scene, road, paint);
  landscape(scene, paint);
  const { car, wheels } = supra(scene, paint);
  const previewMaterial = paint.mat('preview', { transparent: true, side: THREE.DoubleSide, depthWrite: false });
  const preview = mesh(scene, ribbonGeometry(road, 0, 0, 4.8, 0, 0.085, 100), previewMaterial);
  preview.castShadow = false;
  preview.visible = false;
  const controls = new OrbitControls(camera, renderer.domElement);
  controls.enableDamping = false;
  controls.enablePan = true;
  controls.minZoom = 0.65;
  controls.maxZoom = 3.5;
  controls.minPolarAngle = 0.18;
  controls.maxPolarAngle = Math.PI / 2.15;
  controls.target.set(0, 0, 0);
  controls.update();
  controls.addEventListener('change', render);
  let follow = false;
  let interacting = false;
  let distance = 0;
  let previousPreview = -1;
  let previousDistance = -1;
  let disposed = false;
  const onStart = () => { interacting = true; };
  const onEnd = () => { interacting = false; };
  controls.addEventListener('start', onStart);
  controls.addEventListener('end', onEnd);
  const forward = new THREE.Vector3();
  const side = new THREE.Vector3();
  const normal = new THREE.Vector3();
  const orientation = new THREE.Matrix4();
  const delta = new THREE.Vector3();
  function update(frame, presentation = {}) {
    if (disposed) return;
    if (Number.isFinite(presentation.distance_m)) distance = presentation.distance_m / METERS_PER_WORLD_UNIT;
    const sample = road.atDistance(distance);
    car.position.set(...sample.position);
    car.position.y += 0.085;
    forward.set(...sample.tangent);
    side.crossVectors(forward, UP).normalize();
    normal.crossVectors(side, forward).normalize();
    orientation.makeBasis(forward, normal, side);
    car.quaternion.setFromRotationMatrix(orientation);
    // Wheel phase is illustrative, but is a pure function of replay distance.
    wheels.forEach(wheel => { wheel.rotation.z = -distance / 0.62; });
    const previewLength = previewWorldLength(presentation.preview_m, road.length);
    preview.visible = previewLength > 0;
    if (preview.visible && (distance !== previousDistance || previewLength !== previousPreview)) {
      const next = ribbonGeometry(road, distance, previewLength, 4.8, 0, 0.085, 100);
      preview.geometry.dispose();
      preview.geometry = next;
    }
    previousDistance = distance;
    previousPreview = previewLength;
    if (follow && !interacting) {
      delta.copy(car.position).sub(controls.target).multiplyScalar(0.075);
      camera.position.add(delta);
      controls.target.add(delta);
      controls.update();
    }
    render();
  }
  update(null);
  return {
    update,
    // The loop is short compared with a real drive, so the car laps it. Exposed
    // so the UI can SHOW the repetition rather than only assert the road is
    // illustrative: a viewer who sees lap 9 of 15 cannot read the hill as the
    // recorded route.
    loopLength_m: road.length * METERS_PER_WORLD_UNIT,
    setFollow(value) { follow = Boolean(value); },
    // 'light' (the default) or 'dark'; anything else falls back to light. It
    // re-tints and re-renders only -- the car keeps its place on the road, the
    // camera and follow state keep theirs, and the preview ribbon keeps the
    // geometry it already has.
    setTheme(name) {
      if (disposed) return;
      view.setTheme(name);
      render();
    },
    resetCamera() {
      if (disposed) return;
      follow = false;
      camera.position.set(50, 46, 60);
      camera.zoom = 1;
      camera.updateProjectionMatrix();
      controls.target.set(0, 0, 0);
      controls.update();
      render();
    },
    zoom(factor) {
      if (disposed || !Number.isFinite(factor) || factor <= 0) return;
      camera.zoom = THREE.MathUtils.clamp(camera.zoom * factor, controls.minZoom, controls.maxZoom);
      camera.updateProjectionMatrix();
      render();
    },
    dispose() {
      if (disposed) return;
      disposed = true;
      controls.removeEventListener('change', render);
      controls.removeEventListener('start', onStart);
      controls.removeEventListener('end', onEnd);
      controls.dispose();
      view.dispose();
    },
  };
}

// Cool -> warm -> hot, and a separate grey for "no value". The SHAPE is the
// meaning and does not change with the theme: the first half of the range
// crosses from cool to warm, the second half adds hot on top of it, and the
// endpoints are the only thing a theme moves -- brighter ones for the dark
// inset, so the ramp keeps its contrast without keeping its luminance.
const RAMPS = {};
function ramp(theme) {
  const name = themeName(theme);
  if (!RAMPS[name]) {
    RAMPS[name] = Object.fromEntries(['cool', 'warm', 'hot', 'unknown'].map(part => {
      const key = `temp${part[0].toUpperCase()}${part.slice(1)}`;
      return [part, new THREE.Color(entry(name, key).color)];
    }));
  }
  return RAMPS[name];
}
function temperatureColor(material, value, low, high, colors) {
  if (!Number.isFinite(value)) { material.color.copy(colors.unknown); return; }
  const ratio = THREE.MathUtils.clamp((value - low) / (high - low), 0, 1);
  material.color.copy(colors.cool).lerp(colors.warm, Math.min(1, ratio * 2));
  if (ratio > 0.5) material.color.lerp(colors.hot, (ratio - 0.5) * 2);
}

export function createEngineScene(host) {
  const view = stage(host, { extent: 5.9, position: [11, 10, 13], target: [0, 0.7, 0], shadows: false });
  const { scene, render, paint } = view;
  // These four carry a temperature, so the palette only seeds them; the ramp
  // owns their colour from the first update onward.
  const block = paint.loose('tempUnknown', { metalness: 0.25 });
  const turbine = paint.loose('tempUnknown', { metalness: 0.4 });
  const coolant = paint.loose('tempUnknown', { metalness: 0.12 });
  const oil = paint.loose('tempUnknown', { metalness: 0.22 });
  const metal = paint.mat('blockMetal', { metalness: 0.45 });
  const dark = paint.mat('engineDark', { metalness: 0.35 });
  const engine = new THREE.Group();
  engine.position.x = -0.6;
  box(engine, [6.3, 1.55, 2.1], block, [0, 0.8, 0]);
  box(engine, [6.55, 0.35, 2.3], metal, [0, 1.77, 0]);
  box(engine, [6.1, 0.28, 1.6], block, [0, 2.07, 0]);
  box(engine, [5.4, 0.48, 1.8], oil, [0, -0.22, 0]);
  for (let i = 0; i < 6; i++) {
    const x = -2.5 + i;
    mesh(engine, new THREE.CylinderGeometry(0.32, 0.32, 0.19, 12), dark, [x, 2.3, 0]);
    pipe(engine, [[x, 1.35, 1.1], [x, 1.1, 1.7], [x * 0.7, 0.85, 2.2]], 0.13, metal);
  }
  pipe(engine, [[-1.8, 0.85, 2.2], [0, 0.85, 2.2], [2, 0.85, 2.2], [2.6, 0.85, 2.7]], 0.21, metal);
  // Two housings connected by one shaft represent a single turbo assembly.
  for (const [z, material] of [[2.6, turbine], [3.8, metal]]) {
    mesh(engine, new THREE.TorusGeometry(0.62, 0.26, 9, 20), material, [2.55, 1.02, z]);
    const hub = mesh(engine, new THREE.CylinderGeometry(0.25, 0.25, 0.23, 12), dark, [2.55, 1.02, z]);
    hub.rotation.x = Math.PI / 2;
  }
  const shaft = mesh(engine, new THREE.CylinderGeometry(0.1, 0.1, 1.2, 10), dark, [2.55, 1.02, 3.2]);
  shaft.rotation.x = Math.PI / 2;
  pipe(engine, [[2.55, 1.65, 3.8], [1.6, 2.6, 3.8], [-2.8, 2.65, 2.7], [-2.9, 2, 0.75]], 0.18, metal);
  pipe(engine, [[2.9, 0.5, 2.6], [3.9, 0.3, 2.5], [4.7, 0.3, 2.5]], 0.2, metal);
  // Radiator proxy shares the coolant channel; no radiator-metal temperature exists.
  box(engine, [0.42, 2.6, 3], coolant, [-4.5, 0.85, 0]);
  for (let i = 0; i < 9; i++) box(engine, [0.48, 0.055, 2.8], metal, [-4.5, -0.24 + i * 0.27, 0]);
  pipe(engine, [[-4.5, 2, -0.85], [-3.7, 2.6, -1.5], [-2.9, 1.3, -1.1]], 0.17, coolant);
  pipe(engine, [[2.7, 0.5, -1.05], [2.3, -0.3, -1.8], [-4.2, -0.4, -1.8], [-4.5, -0.2, -0.9]], 0.17, coolant);
  mesh(engine, new THREE.CylinderGeometry(0.32, 0.32, 0.68, 12), oil, [1.5, 0.4, -1.4]);
  scene.add(engine);
  let disposed = false;
  let shown = null;
  function repaint() {
    const colors = ramp(view.theme());
    temperatureColor(block, shown?.block_c, 60, 180, colors);
    temperatureColor(turbine, shown?.turbine_c, 250, 1000, colors);
    temperatureColor(coolant, shown?.coolant_c, 65, 120, colors);
    temperatureColor(oil, shown?.oil_c, 65, 160, colors);
  }
  function update(frame) {
    if (disposed) return;
    shown = frame;
    repaint();
    render();
  }
  update(null);
  return {
    update,
    // Same contract as the world scene: re-tint, re-ramp the four temperature
    // nodes at the values they are already showing, re-render.
    setTheme(name) {
      if (disposed) return;
      view.setTheme(name);
      repaint();
      render();
    },
    dispose() { if (disposed) return; disposed = true; view.dispose(); },
  };
}
