// The chase view without a browser: stage() needs WebGL, so these tests hand
// createChaseScene a stand-in stage that owns a real THREE.Scene and nothing
// else, and read the scene graph. What they cannot see (pixels, the camera
// framing, the shadows) is checked by eye in the browser (Task 11).
//
// Three.js lives in app/node_modules (npm install in app/, which
// app\start-simulation.ps1 runs when it has to vendor Three.js); .gitignore
// excludes it. Without it every test here SKIPS and says why. With it, a
// broken agent-scene.mjs FAILS: only the 'three' import is guarded.
import test from 'node:test';
import assert from 'node:assert/strict';
import { createEpisodeRoad, CAR_OFFSET, CAR_HALF_WIDTH, LANE_W, ROAD_W, M_PER_UNIT } from './agent-view.mjs';

let THREE = null;
try { THREE = await import('three'); } catch { /* reported through SKIP */ }
const SKIP = THREE ? false : 'three is not installed in app/node_modules (run: cd app; npm install)';
let S = null;
let lab = null;
let loadError = null;
if (THREE) {
  try { lab = await import('./scene.mjs'); S = await import('./agent-scene.mjs'); } catch (err) { loadError = err; }
}
const api = () => { assert.ok(S, `agent-scene.mjs must load: ${loadError?.message}`); return S; };
const close = (a, b, tol, msg) => assert.ok(Math.abs(a - b) <= tol, `${msg}: ${a} vs ${b}`);

// A route built the way app/agent_trace.route() builds one: launch from rest,
// flat, then 13.314 % from step 20.
function makeRoad() {
  const v = Array.from({ length: 60 }, (_, k) => Math.min(36.1, 2 * k));
  const g = v.map((_, k) => (k >= 20 ? 0.13314 : 0));
  const s = [0], x = [0], z = [0];
  for (let k = 0; k < v.length - 1; k++) {
    const th = Math.atan(g[k]);
    s.push(s[k] + v[k]); x.push(x[k] + v[k] * Math.cos(th)); z.push(z[k] + v[k] * Math.sin(th));
  }
  return { s_m: s, x_m: x, z_m: z, grade_pct: g.map(u => u * 100), speed_kmh: v.map(u => u * 3.6) };
}
const ROUTE = makeRoad();

// Stands in for scene.mjs stage(): same shape, a real Scene, no renderer.
function fakeStage() {
  let theme = 'light';
  const seen = { renders: 0, disposed: false, options: null, view: null };
  const paint = {
    mat: (key, extra = {}) => new THREE.MeshStandardMaterial(extra),
    loose: (key, extra = {}) => new THREE.MeshStandardMaterial(extra),
    glow: (key, extra = {}) => new THREE.MeshBasicMaterial(extra),
    theme: () => theme,
  };
  const make = (host, options) => {
    seen.options = options;
    seen.view = {
      scene: new THREE.Scene(),
      camera: new THREE.OrthographicCamera(),
      renderer: { domElement: { style: {} } },
      render: () => { seen.renders += 1; },
      paint,
      setTheme: name => { theme = name === 'dark' ? 'dark' : 'light'; },
      theme: () => theme,
      dispose: () => { seen.disposed = true; },
    };
    return seen.view;
  };
  return { make, seen, paint };
}
function build(lanes = { sighted: '#0000ff', blind: '#ffaa00' }) {
  const fake = fakeStage();
  const road = createEpisodeRoad(ROUTE);
  const chase = api().createChaseScene({}, road, lanes, { makeStage: fake.make });
  return { chase, road, scene: fake.seen.view.scene, seen: fake.seen };
}

test('the lab car is no wider than CAR_HALF_WIDTH, and the constant is tight', { skip: SKIP }, () => {
  api();
  const { car } = lab.supra(new THREE.Scene(), fakeStage().paint);
  car.updateMatrixWorld(true);
  const body = new THREE.Box3();
  // renderOrder -1 marks scene.mjs glowMesh(): headlight beams and light pools
  // on the road, which are light, not car.
  car.traverse(o => { if (o.isMesh && o.renderOrder !== -1) body.union(new THREE.Box3().setFromObject(o, true)); });
  const half = Math.max(-body.min.z, body.max.z);
  assert.ok(half <= CAR_HALF_WIDTH, `supra is ${half} wide each side, over CAR_HALF_WIDTH`);
  assert.ok(half > CAR_HALF_WIDTH - 0.01, `CAR_HALF_WIDTH is loose: supra measures ${half}`);
});

test('the road slides under two still cars and a still camera', { skip: SKIP }, () => {
  const { chase, road, scene, seen } = build();
  assert.ok(seen.options.extent > 0);
  assert.equal(seen.view.renderer.domElement.style.touchAction, 'pan-y');
  const camera = seen.view.camera.position.clone();
  const world = scene.getObjectByName('agents-world');
  for (const metres of [0, 150, 900, 1e9]) {
    chase.update({ distance_m: metres });
    const p = road.atDistance(Math.min(road.length, metres / M_PER_UNIT)).position;
    assert.deepEqual(world.position.toArray(), [-p[0], -p[1], 0], `world at ${metres} m`);
    assert.deepEqual(scene.getObjectByName('car-sighted').position.toArray(), [0, 0.085, CAR_OFFSET]);
    assert.deepEqual(scene.getObjectByName('car-blind').position.toArray(), [0, 0.085, -CAR_OFFSET]);
    assert.ok(seen.view.camera.position.equals(camera), 'the camera moved');
  }
  const held = world.position.clone();
  chase.update({ distance_m: NaN });
  assert.ok(world.position.equals(held), 'a non-finite distance moved the road');
});

test('both cars pitch to the true slope, the same way', { skip: SKIP }, () => {
  const { chase, scene } = build();
  chase.update({ distance_m: 100 });                        // flat
  let fwd = new THREE.Vector3(1, 0, 0).applyQuaternion(scene.getObjectByName('car-sighted').quaternion);
  close(fwd.y, 0, 1e-12, 'flat pitch');
  const climbM = (ROUTE.s_m[30] + ROUTE.s_m[31]) / 2;        // on the 13.314 % climb
  chase.update({ distance_m: climbM });
  for (const name of ['car-sighted', 'car-blind']) {
    fwd = new THREE.Vector3(1, 0, 0).applyQuaternion(scene.getObjectByName(name).quaternion);
    close(fwd.y / fwd.x, 0.13314, 1e-9, `${name} rise over run`);
    close(fwd.z, 0, 1e-12, `${name} yaw`);
  }
});

test('preview posts stand at the marks on the sighted edge, coloured by grade, and hide without marks', { skip: SKIP }, () => {
  const { chase, road, scene } = build();
  chase.update({ distance_m: 300, marks: [{ s_m: 400, grade_pct: 13.3 }, { s_m: 700, grade_pct: 0 }, { s_m: NaN, grade_pct: null }] });
  const posts = [0, 1, 2].map(i => scene.getObjectByName(`preview-post-${i}`));
  assert.deepEqual(posts.map(p => p.visible), [true, true, false]);
  const q = road.atDistance(400 / M_PER_UNIT).position;
  close(posts[0].position.x, q[0], 1e-9, 'post along the road');
  close(posts[0].position.y, q[1] + 0.04, 1e-9, 'post on the road surface');
  assert.ok(posts[0].position.z - 0.07 > CAR_OFFSET + CAR_HALF_WIDTH, 'a post stands inside the sighted car');
  assert.ok(posts[0].position.z + 0.07 <= ROAD_W / 2, 'a post stands off the road');
  const light = p => p.getObjectByName('flag').material.color.getHSL({}).l;
  assert.ok(light(posts[0]) < light(posts[1]), 'a steeper grade must read stronger on the light theme');
  chase.update({ distance_m: 310 });
  assert.deepEqual(posts.map(p => p.visible), [false, false, false]);
});

test('lane tints sit on their own side in the lane colours, and follow setTheme', { skip: SKIP }, () => {
  const { chase, scene } = build();
  const lanes = { sighted: scene.getObjectByName('lane-sighted'), blind: scene.getObjectByName('lane-blind') };
  for (const [name, sign] of [['sighted', 1], ['blind', -1]]) {
    const g = lanes[name].geometry;
    g.computeBoundingBox();
    close(g.boundingBox.min.z, sign * CAR_OFFSET - LANE_W / 2, 1e-6, `${name} min z`);
    close(g.boundingBox.max.z, sign * CAR_OFFSET + LANE_W / 2, 1e-6, `${name} max z`);
  }
  assert.equal(lanes.sighted.material.color.getHexString(), '0000ff');
  assert.equal(lanes.blind.material.color.getHexString(), 'ffaa00');
  chase.setTheme('dark', { sighted: ' #123456 ' });          // getComputedStyle keeps the space
  assert.equal(lanes.sighted.material.color.getHexString(), '123456');
  assert.equal(lanes.blind.material.color.getHexString(), 'ffaa00');
});

test('dispose is final and idempotent', { skip: SKIP }, () => {
  const { chase, seen } = build();
  chase.dispose();
  chase.dispose();
  assert.equal(seen.disposed, true);
  const renders = seen.renders;
  chase.update({ distance_m: 50 });
  chase.setTheme('dark');
  assert.equal(seen.renders, renders);
});

// On a 13 % grade the road behind the cars sinks below the grid's plane, and a
// depth-tested grid drew its lines across the road and both lane tints. The
// grid is a BACKDROP: opaque (so it is not sorted after the road), never
// depth-tested, never writing depth, and first in the opaque pass, so the
// road, the verge and the cars always paint over it.
test('the grid is a backdrop: drawn first, never depth-tested, never sorted as transparent', { skip: SKIP }, () => {
  const { chase, scene } = build();
  const grid = scene.getObjectByName('grid');
  assert.ok(grid, 'no grid');
  assert.equal(grid.renderOrder, -1, 'the grid must draw before everything else');
  assert.equal(grid.material.depthTest, false, 'a depth-tested grid draws over the road where the road sinks below it');
  assert.equal(grid.material.depthWrite, false, 'the grid must leave the depth buffer to the road and the cars');
  assert.equal(grid.material.transparent, false, 'a transparent grid is sorted AFTER the opaque road');
  for (const name of ['verge', 'road', 'lane-sighted', 'lane-blind', 'centre-dashes']) {
    assert.ok(scene.getObjectByName(name).renderOrder > grid.renderOrder, `${name} must draw after the grid`);
  }
  chase.setTheme('dark');
  assert.equal(grid.material.transparent, false, 'setTheme must not make the grid transparent again');
});

// createChaseScene builds a WebGL stage before anything else. If a later step
// throws, the page never receives the scene and cannot dispose it, so the
// scene disposes its own stage before the error goes on to the page.
test('a scene that fails half-built disposes its stage and rethrows', { skip: SKIP }, () => {
  const fake = fakeStage();
  const mat = fake.paint.mat;
  fake.paint.mat = (key, extra) => {
    if (key === 'roadLine') throw new Error('no road line');
    return mat(key, extra);
  };
  assert.throws(() => api().createChaseScene({}, createEpisodeRoad(ROUTE), undefined, { makeStage: fake.make }),
    /no road line/);
  assert.equal(fake.seen.disposed, true, 'the half-built stage was left behind');
});
