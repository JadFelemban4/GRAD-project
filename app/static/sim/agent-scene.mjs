// The /agents chase view: two cars side by side on the episode's own road.
//
// Built from the lab's own parts (stage, ribbonGeometry and supra, exported by
// scene.mjs for this page; design section 11 Q2), so the car is the lab's car.
// It draws; it never computes. Every position comes from createEpisodeRoad()
// (agent-view.mjs), which reads the Python route, and every colour of a
// preview post comes from the grade the sighted agent was given.
//
// FLOATING ORIGIN. The cars and the camera never move. Each update translates
// the world group by minus the road point under the cars, so the road slides
// under them. The camera is stage()'s orthographic camera, static, and the
// sun's shadow box (±45 units about the origin, scene.mjs stage()) therefore
// always covers the cars. One world unit is M_PER_UNIT metres on BOTH axes, so
// the slope on screen is the true slope (the caption says so); the car is not
// to scale (about 6.5 units, 65 m, long).
import * as THREE from 'three';
import { stage, ribbonGeometry, supra } from './scene.mjs';
import { CAR_OFFSET, LANE_W, ROAD_W, gradeRamp } from './agent-view.mjs';

const UP = new THREE.Vector3(0, 1, 0);
// Camera: a little behind the cars (-x), above them, and well out on the
// sighted car's side (+z), so the preview posts at the sighted road edge are
// never behind a car and the climb shows as the road tilting against the grid.
// Chosen by rendering the real episode-1 road flat (k = 130) and on the climb
// (k = 200): a camera more behind the cars made the two look the same. The
// extent is half the view height in world units: 11 units is about 110 m.
const EXTENT = 11;
const CAMERA_POSITION = [-6, 9, 26];
const CAMERA_TARGET = [8, 0, 0];
const ROAD_SEGMENTS = 719;        // one per episode step (design section 5)
const ROAD_LIFT = 0.04;           // ribbonGeometry's default lift
const CAR_LIFT = 0.085;           // as scene.mjs createScene: the car above the road point
const WHEEL_RADIUS = 0.62;        // supra()'s tyre radius; wheel phase = distance / radius
const DASH_EVERY_M = 20;
const DASH_LEN_M = 6;
const POST_Z = ROAD_W / 2 - 0.15; // the sighted car's road edge, outside its car
const POST_H = 1.4;
const GRID_STEP = 2;              // 20 m
// A horizontal reference under the cars, so a climb reads as a climb. It is a
// BACKDROP, opaque and drawn first (see the grid below), so the colours are
// the old 0.8-opacity lines already blended over --world-bg (#e7eddf light,
// #171d1e dark): 0.8 x 0xc8cbbd + 0.2 x 0xe7eddf, and the same for dark.
const GRID = { light: 0xced2c4, dark: 0x343f3c };
// Preview posts: one hue (violet, neither red nor green, and apart from the
// blue and amber lane colours), pale at a flat road and deep at 16 %. On the
// dark theme it runs the other way, dim to bright, so steeper stays stronger.
const RAMP = {
  light: { low: 0xcfc4e8, high: 0x4b2e83, unknown: 0x9aa59e },
  dark: { low: 0x4a3f66, high: 0xd6c6ff, unknown: 0x5d6763 },
};
const LANE_OPACITY = 0.3;

function laneMaterial(colour) {
  const material = new THREE.MeshStandardMaterial({
    color: 0xffffff, transparent: true, opacity: LANE_OPACITY, depthWrite: false, side: THREE.DoubleSide, roughness: 0.9,
  });
  setColour(material, colour);
  return material;
}
function setColour(material, colour) {
  const text = typeof colour === 'string' ? colour.trim() : colour;
  if (text === '' || text === undefined || text === null) return;
  material.color.set(text);
}

/**
 * createChaseScene(host, episodeRoad, lanes) -> { update, setTheme, dispose }
 *
 *   episodeRoad  createEpisodeRoad(road) from agent-view.mjs
 *   lanes        { sighted, blind }: CSS colours (the --agent-* tokens)
 *   update({ distance_m, marks })  distance along the route in metres; marks is
 *                [{ s_m, grade_pct }], one per preview horizon, or [] / absent
 *                to hide the posts. A non-finite distance keeps the last one.
 *   setTheme(name, lanes)  'light' | 'dark', and the lane colours re-read
 *
 * `options.makeStage` exists for agent-scene.test.mjs, which runs under node
 * without WebGL; the page never passes it.
 */
export function createChaseScene(host, episodeRoad, lanes = { sighted: '#2f6db0', blind: '#b7791f' }, options = {}) {
  const makeStage = options.makeStage ?? stage;
  const view = makeStage(host, { extent: EXTENT, position: CAMERA_POSITION, target: CAMERA_TARGET });
  // A step below can throw after the stage (renderer, canvas, WebGL context)
  // exists. The page then never receives a scene and cannot dispose it, so
  // the stage is disposed here before the error goes on to the page.
  try {
    return buildChase(view, episodeRoad, lanes);
  } catch (err) {
    view.dispose();
    throw err;
  }
}

// Everything createChaseScene puts on its stage, and the scene's methods.
function buildChase(view, episodeRoad, lanes) {
  const { scene, render, paint } = view;
  // stage() stops touch scrolling on its canvas (the lab has orbit controls).
  // This camera is fixed, so a phone must still scroll past the view.
  if (view.renderer?.domElement?.style) view.renderer.domElement.style.touchAction = 'pan-y';
  const road = episodeRoad;
  const M = road.mPerUnit;
  let colours = { ...lanes };
  let theme = view.theme();

  // ---- the world: everything that slides under the still cars
  const world = new THREE.Group();
  world.name = 'agents-world';
  scene.add(world);
  const addRibbon = (name, width, offset, lift, material) => {
    const item = new THREE.Mesh(ribbonGeometry(road, 0, road.length, width, offset, lift, ROAD_SEGMENTS), material);
    item.name = name;
    item.receiveShadow = true;
    world.add(item);
    return item;
  };
  addRibbon('verge', ROAD_W + 1.2, 0, 0, paint.mat('verge', { side: THREE.DoubleSide }));
  addRibbon('road', ROAD_W, 0, ROAD_LIFT, paint.mat('road', { side: THREE.DoubleSide }));
  const lineMaterial = paint.mat('roadLine', { side: THREE.DoubleSide });
  for (const side of [-1, 1]) addRibbon(`edge-${side}`, 0.1, side * (ROAD_W / 2 - 0.2), 0.065, lineMaterial);
  const laneSighted = addRibbon('lane-sighted', LANE_W, CAR_OFFSET, 0.05, laneMaterial(colours.sighted));
  const laneBlind = addRibbon('lane-blind', LANE_W, -CAR_OFFSET, 0.05, laneMaterial(colours.blind));

  // Centre dashes every 20 m: one InstancedMesh, one draw call.
  const dashLength = DASH_LEN_M / M;
  const dashGeometry = new THREE.PlaneGeometry(dashLength, 0.14);
  dashGeometry.rotateX(-Math.PI / 2);
  const dashCount = Math.floor(road.length * M / DASH_EVERY_M) + 1;
  const dashes = new THREE.InstancedMesh(dashGeometry, lineMaterial, dashCount);
  dashes.name = 'centre-dashes';
  const place = new THREE.Matrix4();
  const quaternion = new THREE.Quaternion();
  const unit = new THREE.Vector3(1, 1, 1);
  const zAxis = new THREE.Vector3(0, 0, 1);
  for (let i = 0; i < dashCount; i++) {
    const { position: p, tangent: t } = road.atDistance(i * DASH_EVERY_M / M + dashLength / 2);
    quaternion.setFromAxisAngle(zAxis, Math.atan2(t[1], t[0]));
    place.compose(new THREE.Vector3(p[0], p[1] + 0.06, 0), quaternion, unit);
    dashes.setMatrixAt(i, place);
  }
  dashes.instanceMatrix.needsUpdate = true;
  world.add(dashes);

  // Preview posts, grown on demand to however many horizons the page sends
  // (engine_env.PREVIEW_S has four today; this file never assumes that).
  const posts = [];
  const poleMaterial = paint.mat('post');
  const poleGeometry = new THREE.CylinderGeometry(0.07, 0.07, POST_H, 8);
  const flagGeometry = new THREE.BoxGeometry(0.7, 0.4, 0.08);
  const post = i => {
    while (posts.length <= i) {
      const group = new THREE.Group();
      group.name = `preview-post-${posts.length}`;
      const pole = new THREE.Mesh(poleGeometry, poleMaterial);
      pole.position.y = POST_H / 2;
      const flag = new THREE.Mesh(flagGeometry, new THREE.MeshStandardMaterial({ roughness: 0.6 }));
      flag.name = 'flag';
      flag.position.set(0.35, POST_H - 0.2, 0);
      group.add(pole, flag);
      group.visible = false;
      world.add(group);
      posts.push({ group, flag });
    }
    return posts[i];
  };
  let shownMarks = [];
  const placePosts = () => {
    const ramp = RAMP[theme] ?? RAMP.light;
    const count = Math.max(posts.length, shownMarks.length);
    for (let i = 0; i < count; i++) {
      const { group, flag } = post(i);
      const mark = shownMarks[i];
      if (!mark || !Number.isFinite(mark.s_m)) { group.visible = false; continue; }
      const p = road.atDistance(mark.s_m / M).position;
      group.position.set(p[0], p[1] + ROAD_LIFT, POST_Z);
      const f = gradeRamp(mark.grade_pct);
      if (f === null) flag.material.color.set(ramp.unknown);
      else flag.material.color.set(ramp.low).lerp(new THREE.Color(ramp.high), f);
      group.visible = true;
    }
  };

  // ---- the grid: in the scene root, shifted by the fraction of a cell so its
  // lines stay put on the ground as the road slides.
  //
  // A BACKDROP. On a climb the road behind the cars sinks below the grid's
  // plane, and a depth-tested grid drew its lines across the road and both
  // lane tints. So it never tests or writes depth, it is opaque (a transparent
  // grid is sorted AFTER the opaque road), and renderOrder -1 puts it first in
  // the opaque pass: the road, the verge and the cars always paint over it.
  const gridPoints = [];
  for (let x = -40; x <= 60; x += GRID_STEP) gridPoints.push(x, 0, -20, x, 0, 20);
  for (let z = -20; z <= 20; z += GRID_STEP) gridPoints.push(-40, 0, z, 60, 0, z);
  const gridGeometry = new THREE.BufferGeometry();
  gridGeometry.setAttribute('position', new THREE.Float32BufferAttribute(gridPoints, 3));
  const gridMaterial = new THREE.LineBasicMaterial({
    color: GRID[theme] ?? GRID.light, transparent: false, depthTest: false, depthWrite: false,
  });
  const grid = new THREE.LineSegments(gridGeometry, gridMaterial);
  grid.name = 'grid';
  grid.renderOrder = -1;
  scene.add(grid);

  // ---- the two cars: same s, same pitch, ±CAR_OFFSET across the road.
  const cars = [['car-sighted', CAR_OFFSET], ['car-blind', -CAR_OFFSET]].map(([name, z]) => {
    const made = supra(scene, paint);
    made.car.name = name;
    made.car.position.set(0, CAR_LIFT, z);
    return made;
  });

  const forward = new THREE.Vector3();
  const side = new THREE.Vector3();
  const normal = new THREE.Vector3();
  const orientation = new THREE.Matrix4();
  let distance = 0;          // world units along the route
  let disposed = false;

  function update({ distance_m, marks } = {}) {
    if (disposed) return;
    if (Number.isFinite(distance_m)) distance = Math.min(road.length, Math.max(0, distance_m / M));
    const { position: p, tangent } = road.atDistance(distance);
    world.position.set(-p[0], -p[1], 0);
    grid.position.set(-(((p[0] % GRID_STEP) + GRID_STEP) % GRID_STEP), -0.02, 0);
    forward.set(...tangent);
    side.crossVectors(forward, UP).normalize();
    normal.crossVectors(side, forward).normalize();
    orientation.makeBasis(forward, normal, side);
    for (const { car, wheels } of cars) {
      car.quaternion.setFromRotationMatrix(orientation);
      wheels.forEach(wheel => { wheel.rotation.z = -distance / WHEEL_RADIUS; });
    }
    shownMarks = Array.isArray(marks) ? marks : [];
    placePosts();
    render();
  }

  function setTheme(name, nextLanes) {
    if (disposed) return;
    view.setTheme(name);
    theme = view.theme();
    if (nextLanes) colours = { ...colours, ...nextLanes };
    setColour(laneSighted.material, colours.sighted);
    setColour(laneBlind.material, colours.blind);
    gridMaterial.color.set(GRID[theme] ?? GRID.light);
    placePosts();
    render();
  }

  update({ distance_m: 0 });
  return {
    update,
    setTheme,
    dispose() {
      if (disposed) return;
      disposed = true;
      view.dispose();
    },
  };
}
