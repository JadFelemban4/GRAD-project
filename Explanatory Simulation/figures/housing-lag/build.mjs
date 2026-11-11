// Fig 1 of the learning lab: the turbine housing lags the gas that heats it.
//
// A hot-gas test stand drawn with the Anatomy kit (../kit, MIT): a burner that
// stands in for the engine drives gas through a duct into a turbine housing on
// a pedestal, and a two-pen strip recorder draws the gas and the housing metal
// on moving paper. Every number comes from params.json (export_params.py, from
// plant.py and thermal.py) through src/model/housing-lag.mjs, which the page
// runs live; housing-lag.test.mjs proves that model equals ThermalNetwork.
//
//   node figures/housing-lag/build.mjs     writes public/figures/housing-lag.html
//
// The page reads ?lang=ar|en&theme=dark|light (the lab passes its own), falls
// back to the lab's saved preferences, and tells a parent frame its height.

import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import * as k from "../kit/iso-kit.mjs";
import { inputsOf, settleOf, tauOf } from "../../src/model/housing-lag.mjs";
import { copyFor } from "./copy.mjs";

const HERE = dirname(fileURLToPath(import.meta.url));
const LAB = resolve(HERE, "..", "..");
const OUT = join(LAB, "public", "figures", "housing-lag.html");
const PARAMS = JSON.parse(readFileSync(join(HERE, "params.json"), "utf8"));
const inline = (file) => readFileSync(file, "utf8").replace(/^export /gm, "");

// ---- the numbers -----------------------------------------------------------
const SPEED = 10; // model seconds per real second
const SPAN = 500; // model seconds across the paper
const T_TOP = 1000; // °C at the top of the paper

const TURBINE = PARAMS.turbine;
const LIT = inputsOf(PARAMS, true);
const OFF = inputsOf(PARAMS, false);
const TAU_ON = tauOf(TURBINE, LIT.mdotExhGps);
const TAU_OFF = tauOf(TURBINE, OFF.mdotExhGps);
const SETTLE_ON = settleOf(TURBINE, LIT.mdotExhGps, LIT.egtK, LIT.tAmbK) - 273.15;
const fixed = (value, digits = 0) => value.toFixed(digits);
const COPY = copyFor({
  gas: `${fixed(PARAMS.engine.egt_c)} °C`,
  flow: `${fixed(PARAMS.engine.mdot_exh_gps, 1)} g/s`,
  rpm: `${fixed(PARAMS.point.rpm)} rpm`,
  map: `${fixed(PARAMS.point.map_kpa)} kPa`,
  amb: `${fixed(PARAMS.point.ambient_c)} °C`,
  dt: `${TURBINE.dt_sub_max} s`,
  settle: `${fixed(SETTLE_ON)} °C`,
  tauOn: `${fixed(TAU_ON)} s`,
  tauOff: `${fixed(TAU_OFF)} s`,
  c: `${fixed(TURBINE.c_turb)} J/K`,
  speed: String(SPEED),
});

// ---- the world (units of about 1 px, z up) ----------------------------------
const WIDTH = 600;
const HEIGHT = 400;

const PLATE = { x: -178, y: -58, w: 362, d: 130, r: 8 };
const PLATE_H = 10;
const FOOT_H = 5;

const BURNER = { x: -166, y: -48, w: 58, d: 50, r: 4 };
const BURNER_Z = 4;
const BURNER_TOP = 56;
const KNOB = { off: -152, on: -128, y: -26.5, r: 4.6, h: 5.5 };
const LAMP = [-118, -38];

const HOUSING = { cx: -22, cy: 8, r1: 33, r0: 15, z0: 18, z1: 44, inlet: -58 };
const DUCT = { x0: -104, x1: -66, y0: HOUSING.cy - HOUSING.r1, y1: HOUSING.cy - HOUSING.r0, z0: 22, z1: 40 };
const OUTLET = { r: 10.5, top: 56, flange: 13.5, lip: 59, bore: 8 };
const GAS_PROBE = [-84, (DUCT.y0 + DUCT.y1) / 2];
const HOUSING_PROBE = [HOUSING.cx + 6, HOUSING.cy + 20];

const RECORDER = { x: 32, y: -18, w: 140, d: 50, r: 4 };
const RECORDER_TOP = 92;
const FACE = RECORDER.y + RECORDER.d; // the front face, y = 32
const PAPER = { x0: 43, x1: 147, z0: 24, z1: 82 };
const RODS = { gas: { x: 154, y: FACE + 2.2 }, housing: { x: 160, y: FACE + 7 } };
const POSTS = { gas: 52, housing: 66 };

const P = k.fitProjection(
  [
    ...k.boxCorners(PLATE, -PLATE_H - FOOT_H, 0),
    ...k.boxCorners(RECORDER, 0, RECORDER_TOP + 5),
    [BURNER.x, BURNER.y, BURNER_TOP + 6],
    [HOUSING.cx, HOUSING.cy, OUTLET.lip],
    [RODS.housing.x + 3, RODS.housing.y + 2, PAPER.z1 + 5],
  ],
  WIDTH,
  HEIGHT,
  { pad: 22, azimuth: 56, elevation: 38 },
);

const at = (point) => k.iso(point, P);
const S = (paths, style) => k.solidSvg(paths, style);
const L = (d, style) => k.lineSvg(d, style);
const D = (points, style) => k.dotsSvg(points, style);
const path3 = (points, closed = false) => k.pathOf(points.map(at), closed);
const byDepth = (points) => [...points].sort((a, b) => k.depthOf([a[0], a[1], 0], P) - k.depthOf([b[0], b[1], 0], P));
// A rectangle drawn in the plane of a face whose normal is +y, from x0 to x1 and z0 to z1.
const faceRect = (y, x0, x1, z0, z1) => path3([[x0, y, z0], [x1, y, z0], [x1, y, z1], [x0, y, z1]], true);
// The same with rounded ends along x, for slots and vents.
function faceSlot(y, x0, x1, z0, z1) {
  const r = (z1 - z0) / 2;
  const points = [];
  for (let step = 0; step <= 8; step++) {
    const a = -Math.PI / 2 + (step / 8) * Math.PI;
    points.push([x1 - r + r * Math.cos(a), y, z0 + r + r * Math.sin(a)]);
  }
  for (let step = 0; step <= 8; step++) {
    const a = Math.PI / 2 + (step / 8) * Math.PI;
    points.push([x0 + r + r * Math.cos(a), y, z0 + r + r * Math.sin(a)]);
  }
  return path3(points, true);
}

// ---- the plate ---------------------------------------------------------------
function plate() {
  const out = [`<path class="iso-halo" d="${k.haloOf(PLATE, -PLATE_H - FOOT_H, PLATE_H, P)}"/>`];
  for (const [x, y] of byDepth(k.corners(PLATE, 24))) {
    out.push(S(k.cylinder(x, y, 7, -PLATE_H - FOOT_H, 1.6, P, 28), { tone: "lo" }));
    out.push(S(k.cylinder(x, y, 5.4, -PLATE_H - FOOT_H + 1.6, FOOT_H - 1.6, P, 28), { tone: "mid" }));
  }
  out.push(S(k.slabOf(PLATE, -PLATE_H, PLATE_H, P, 8, 1.6), { tone: "mid" }));
  out.push(L(k.planOutline(k.insetPlan(PLATE, 5), 0, P), { tone: "lo" }));
  const screws = k.corners(PLATE, 10);
  out.push(L(screws.map(([x, y]) => k.ring(x, y, 2.2, 0, P, 16)).join(""), { tone: "lo" }));
  out.push(D(screws.map(([x, y]) => at([x, y, 0])), { size: 0.5 }));
  const label = { x: PLATE.x + 12, y: PLATE.y + PLATE.d - 20, w: 40, d: 10, r: 1.2 };
  out.push(S(k.slabOf(label, 0, 0.8, P, 3), { tone: "lo", crease: "none" }));
  out.push(L(k.planOutline(k.insetPlan(label, 1.4), 0.8, P, 3), { tone: "faint" }));
  out.push(L(k.lineOnTop([label.x + 4, label.y + 3.4], [label.x + 26, label.y + 3.4], 0.8, P), { tone: "lo", free: true }));
  out.push(L(k.lineOnTop([label.x + 4, label.y + 6.6], [label.x + 18, label.y + 6.6], 0.8, P), { tone: "lo", free: true }));
  out.push(D([at([label.x + 2.2, label.y + 5, 0.8]), at([label.x + label.w - 2.2, label.y + 5, 0.8])], { size: 0.42 }));
  return out.join("");
}

// ---- the burner: it stands in for the engine ------------------------------------
function burner() {
  const out = [];
  const front = BURNER.y + BURNER.d;
  out.push(S(k.slabOf(k.insetPlan(BURNER, -1.2), 0, BURNER_Z, P, 4, 0.5), { tone: "lo" }));
  out.push(
    S(k.slabOf(BURNER, BURNER_Z, BURNER_TOP - BURNER_Z, P, 4, 1.2), {
      tone: "mid",
      inner: L(k.sideSeam(BURNER, BURNER_TOP - 9, P, 4), { tone: "faint" }),
    }),
  );
  // The sight glass: the flame shows here while the burner is lit.
  const glass = { x0: BURNER.x + 12, x1: BURNER.x + 38, z0: 22, z1: 36 };
  out.push(`<path class="hl-flame" data-part="flame" d="${faceRect(front, glass.x0, glass.x1, glass.z0, glass.z1)}"/>`);
  out.push(L(faceRect(front, glass.x0 - 1.5, glass.x1 + 1.5, glass.z0 - 1.5, glass.z1 + 1.5), { tone: "lo" }));
  out.push(L(faceRect(front, glass.x0, glass.x1, glass.z0, glass.z1), { tone: "mid" }));
  out.push(D([[glass.x0 - 0.3, glass.z0 - 0.3], [glass.x1 + 0.3, glass.z0 - 0.3], [glass.x0 - 0.3, glass.z1 + 0.3], [glass.x1 + 0.3, glass.z1 + 0.3]].map(([x, z]) => at([x, front, z])), { size: 0.42 }));
  for (const x0 of [0, 14, 28]) out.push(L(faceSlot(front, BURNER.x + 10 + x0, BURNER.x + 21 + x0, 9, 12.4), { tone: "lo" }));
  // The control on top: a knob in a slot, off at the back end, lit at the front end.
  const top = BURNER_TOP;
  const slot = { x: KNOB.off - 7, y: KNOB.y - 3.6, w: KNOB.on - KNOB.off + 14, d: 7.2, r: 3.6 };
  out.push(S(k.slabOf(k.insetPlan(slot, -2.2), top, 0.6, P, 6), { tone: "lo", crease: "none" }));
  out.push(L(k.planOutline(slot, top + 0.6, P, 6), { tone: "lo" }));
  const ticks = { x: slot.x + 6, y: slot.y + slot.d + 3, w: slot.w - 12, d: 3.4, r: 0.6 };
  out.push(S(k.slabOf(ticks, top, 0.4, P, 2), { tone: "lo", crease: "none" }));
  out.push(L([KNOB.off, KNOB.on].map((x) => k.lineOnTop([x, ticks.y + 0.2], [x, ticks.y + 2.4], top + 0.4, P)).join(""), { tone: "mid" }));
  out.push(S(k.cylinder(LAMP[0], LAMP[1], 3.4, top, 1.2, P, 24), { tone: "mid" }));
  out.push(S(k.cylinder(LAMP[0], LAMP[1], 2.2, top + 1.2, 1.4, P, 20), { tone: "hi" }));
  out.push(`<path class="hl-lamp" data-part="lamp" d="${k.cylinder(LAMP[0], LAMP[1], 2.2, top + 1.2, 1.4, P, 20).fill}"/>`);
  const plateFor = { x: BURNER.x + 6, y: BURNER.y + 6, w: 26, d: 12, r: 1.2 };
  out.push(S(k.slabOf(plateFor, top, 0.7, P, 3), { tone: "lo", crease: "none" }));
  out.push(L(k.lineOnTop([plateFor.x + 4, plateFor.y + 4], [plateFor.x + 20, plateFor.y + 4], top + 0.7, P), { tone: "lo", free: true }));
  out.push(L(k.lineOnTop([plateFor.x + 4, plateFor.y + 7.6], [plateFor.x + 14, plateFor.y + 7.6], top + 0.7, P), { tone: "lo", free: true }));
  out.push(D([at([plateFor.x + 2, plateFor.y + 6, top + 0.7]), at([plateFor.x + plateFor.w - 2, plateFor.y + 6, top + 0.7])], { size: 0.42 }));
  return out.join("");
}

function knob() {
  const top = BURNER_TOP + 0.6;
  const [x, y] = [KNOB.off, KNOB.y];
  return [
    S(k.cylinder(x, y, 2.2, top, 1.4, P, 16), { tone: "mid" }),
    S(k.cylinder(x, y, KNOB.r, top + 1.4, KNOB.h, P, 32), { tone: "mid" }),
    L(k.knurl(x, y, KNOB.r, top + 1.4, top + 1.4 + KNOB.h, 36, P), { tone: "lo" }),
    L(k.lineOnTop([x, y], [x + KNOB.r - 0.8, y], top + 1.4 + KNOB.h, P), { tone: "hi" }),
    D([at([x, y, top + 1.4 + KNOB.h])], { size: 0.5, tone: "hi" }),
  ].join("");
}

// ---- the duct and the gas thermocouple ------------------------------------------
function duct() {
  const out = [];
  const { x0, x1, y0, y1, z0, z1 } = DUCT;
  const mid = (y0 + y1) / 2;
  // The burner's outlet flange, on its +x face.
  out.push(S(k.slabOf({ x: BURNER.x + BURNER.w, y: mid - 13, w: 4, d: 26, r: 1 }, z0 - 4, z1 - z0 + 8, P, 3, 0.4), { tone: "mid" }));
  out.push(S(k.slabOf({ x: x0, y: y0, w: x1 - x0, d: y1 - y0, r: 1.2 }, z0, z1 - z0, P, 3, 0.6), { tone: "mid", inner: L(k.sideSeam({ x: x0, y: y0, w: x1 - x0, d: y1 - y0, r: 1.2 }, (z0 + z1) / 2, P, 3), { tone: "faint" }) }));
  out.push(D([x0 + 8, x1 - 8].map((x) => at([x, y1, z0 + 2.4])), { size: 0.4 }));
  // The thermocouple that reads the gas: a boss, a thin stem, a knurled head.
  const [px, py] = GAS_PROBE;
  out.push(S(k.cylinder(px, py, 3.2, z1, 2.4, P, 24), { tone: "mid" }));
  out.push(S(k.cylinder(px, py, 1.1, z1 + 2.4, 8, P, 12), { tone: "hi", crease: "none" }));
  out.push(S(k.cylinder(px, py, 2.6, z1 + 10.4, 5.6, P, 24), { tone: "mid" }));
  out.push(L(k.knurl(px, py, 2.6, z1 + 10.4, z1 + 16, 20, P), { tone: "lo" }));
  // Two flanges face to face: the duct's, then the housing's own.
  const flange = { y: mid - 13.5, d: 27, r: 1.2 };
  out.push(S(k.slabOf({ x: x1, y: flange.y, w: 4, ...flange }, HOUSING.z0 - 3, HOUSING.z1 - HOUSING.z0 + 6, P, 3, 0.4), { tone: "mid" }));
  out.push(S(k.slabOf({ x: x1 + 4, y: flange.y, w: 4, ...flange }, HOUSING.z0 - 3, HOUSING.z1 - HOUSING.z0 + 6, P, 3, 0.4), { tone: "hi" }));
  const bolts = [[flange.y + 3, HOUSING.z0], [flange.y + flange.d - 3, HOUSING.z0], [flange.y + 3, HOUSING.z1], [flange.y + flange.d - 3, HOUSING.z1]];
  out.push(D(bolts.map(([y, z]) => at([x1 + 8, y, z])), { size: 0.5, tone: "mid" }));
  return out.join("");
}

// ---- the turbine housing: the subject ------------------------------------------------
const radiusAt = (theta) => HOUSING.r1 - ((HOUSING.r1 - HOUSING.r0) * (theta + Math.PI / 2)) / (2 * Math.PI);
function volute() {
  // The scroll narrows by (r1 - r0) over one turn from the inlet; the inlet's
  // inner wall is the tongue at radius r0. The outline is their union.
  const { cx, cy, r0, r1, inlet } = HOUSING;
  let lo = Math.PI;
  let hi = 1.5 * Math.PI;
  for (let i = 0; i < 60; i++) {
    const mid = (lo + hi) / 2;
    if (radiusAt(mid) * Math.sin(mid) > -r0) lo = mid;
    else hi = mid;
  }
  const end = (lo + hi) / 2;
  const ring = [[inlet, cy - r1]];
  const steps = 120;
  for (let i = 0; i <= steps; i++) {
    const theta = -Math.PI / 2 + ((end + Math.PI / 2) * i) / steps;
    const r = radiusAt(theta);
    ring.push([cx + r * Math.cos(theta), cy + r * Math.sin(theta)]);
  }
  ring.push([inlet, cy - r0]);
  return ring;
}
const VOLUTE = volute();
const CASTING = [];

// A prism over a concave outline. The kit's extrude groups side faces by tone,
// not by depth, so behind the notch between scroll and inlet a far face could
// paint over a near one. This paints each visible side face back to front with
// its own bottom edge, then the top, so the nearer face always wins.
function concavePrism(ring, z0, height, { tone = "hi" } = {}) {
  const count = ring.length;
  let area = 0;
  for (let i = 0; i < count; i++) {
    const [ax, ay] = ring[i];
    const [bx, by] = ring[(i + 1) % count];
    area += ax * by - bx * ay;
  }
  const [vx, vy] = k.towardViewer(P);
  const { sinA, cosA } = k.cameraOf(P);
  const normals = ring.map(([ax, ay], i) => {
    const [bx, by] = ring[(i + 1) % count];
    const length = Math.hypot(bx - ax, by - ay) || 1;
    return area > 0 ? [(by - ay) / length, -(bx - ax) / length] : [-(by - ay) / length, (bx - ax) / length];
  });
  const facing = normals.map(([nx, ny]) => nx * vx + ny * vy > 1e-9);
  const z1 = z0 + height;
  const edge = (a, b, z) => path3([[a[0], a[1], z], [b[0], b[1], z]]);
  const sides = [];
  for (let i = 0; i < count; i++) {
    if (!facing[i]) continue;
    const a = ring[i];
    const b = ring[(i + 1) % count];
    const [nx, ny] = normals[i];
    const shade = Math.min(3, Math.max(0, Math.floor(((nx * -sinA + ny * cosA + 1) / 2) * 4)));
    let lines = edge(a, b, z0);
    if (!facing[(i + count - 1) % count]) lines += path3([[a[0], a[1], z0], [a[0], a[1], z1]]);
    if (!facing[(i + 1) % count]) lines += path3([[b[0], b[1], z0], [b[0], b[1], z1]]);
    sides.push({ depth: k.depthOf([(a[0] + b[0]) / 2, (a[1] + b[1]) / 2, (z0 + z1) / 2], P), quad: path3([[a[0], a[1], z1], [b[0], b[1], z1], [b[0], b[1], z0], [a[0], a[1], z0]], true), shade, lines });
  }
  sides.sort((p, q) => p.depth - q.depth);
  const shell = k.extrude(ring, z0, height, P, { convex: false });
  const crease = ring.map((a, i) => (facing[i] ? edge(a, ring[(i + 1) % count], z1) : "")).join("");
  const rim = ring.map((a, i) => (facing[i] ? "" : edge(a, ring[(i + 1) % count], z1))).join("");
  const parts = [`<path class="iso-fill" d="${shell.fill}"/>`];
  for (const side of sides) parts.push(`<path class="iso-shade" data-shade="${side.shade}" d="${side.quad}"/>`, `<path class="iso-line iso-edge" data-tone="${tone}" d="${side.lines}"/>`);
  parts.push(`<path class="iso-top" d="${shell.top}"/>`, `<path class="iso-line iso-crease" data-tone="lo" d="${crease}"/>`, `<path class="iso-line iso-edge" data-tone="${tone}" d="${rim}"/>`);
  return { svg: `<g class="iso-solid">${parts.join("")}</g>`, fill: shell.fill };
}

// The scroll's inner lip on the casting's face: inset from the outer wall, from
// the inlet flange round one turn until it runs in under the outlet neck.
function scrollLip(inset) {
  const { cx, cy, r1, inlet } = HOUSING;
  const points = [[inlet, cy - r1 + inset], [cx, cy - r1 + inset]];
  for (let i = 1; i <= 160; i++) {
    const theta = -Math.PI / 2 + (2 * Math.PI * i) / 160;
    const r = radiusAt(theta) - inset;
    points.push([cx + r * Math.cos(theta), cy + r * Math.sin(theta)]);
  }
  return k.onTop(points, HOUSING.z1, P);
}

// The turbine wheel seen down the outlet: blades from the hub to the bore,
// swept a little, rebuilt each frame at the wheel's angle.
const WHEEL = { cx: HOUSING.cx, cy: HOUSING.cy, z: OUTLET.lip, hub: 2.6, rim: OUTLET.bore, count: 9, sweep: 0.55 };
function bladesAt(angle) {
  const out = [];
  for (let i = 0; i < WHEEL.count; i++) {
    const a = angle + (i * 2 * Math.PI) / WHEEL.count;
    const points = [];
    for (let s = 0; s <= 4; s++) {
      const r = WHEEL.hub + ((WHEEL.rim - WHEEL.hub) * s) / 4;
      const b = a + (WHEEL.sweep * s) / 4;
      points.push(k.iso([WHEEL.cx + r * Math.cos(b), WHEEL.cy + r * Math.sin(b), WHEEL.z], P));
    }
    out.push(k.pathOf(points));
  }
  return out.join("");
}

function housing() {
  const out = [];
  const { cx, cy, z0, z1 } = HOUSING;
  out.push(S(k.cylinder(cx, cy, 21, 0, 3, P, 48, 0.5), { tone: "lo" }));
  out.push(D([0, 1, 2, 3].map((i) => { const a = Math.PI / 4 + (i * Math.PI) / 2; return at([cx + 18.4 * Math.cos(a), cy + 18.4 * Math.sin(a), 3]); }), { size: 0.5, tone: "mid" }));
  out.push(S(k.cylinder(cx, cy, 14, 3, z0 - 3, P, 48), { tone: "mid", inner: L(k.sideArc(cx, cy, 14, 10, P, 32), { tone: "faint" }) }));
  const body = concavePrism(VOLUTE, z0, z1 - z0, { tone: "hi" });
  CASTING.push(body.fill);
  out.push(body.svg);
  out.push(L(scrollLip(5), { tone: "lo" }));
  const neck = k.cylinder(cx, cy, OUTLET.r, z1, OUTLET.top - z1, P, 56);
  const lip = k.cylinder(cx, cy, OUTLET.flange, OUTLET.top, OUTLET.lip - OUTLET.top, P, 64, 0.6);
  CASTING.push(neck.fill, lip.fill);
  out.push(S(neck, { tone: "hi", inner: L(k.sideArc(cx, cy, OUTLET.r, z1 + 5, P, 32), { tone: "faint" }) }));
  out.push(S(lip, { tone: "hi" }));
  out.push(`<path class="hl-glow" data-part="glow" d="${CASTING.join("")}"/>`);
  const bore = k.ring(cx, cy, OUTLET.bore, OUTLET.lip, P, 64);
  out.push(`<defs><clipPath id="hl-bore"><path d="${bore}"/></clipPath></defs>`);
  out.push(`<g clip-path="url(#hl-bore)"><path class="hl-void" d="${bore}"/>${L(bladesAt(0), { tone: "mid" }).replace("<path ", '<path data-part="blades" ')}<path class="hl-hub" d="${k.ring(cx, cy, WHEEL.hub, WHEEL.z, P, 24)}"/></g>`);
  out.push(L(bore, { tone: "mid" }));
  out.push(L(k.ring(cx, cy, OUTLET.bore + 1.6, OUTLET.lip, P, 48), { tone: "faint" }));
  out.push(D([0, 1, 2, 3, 4, 5].map((i) => { const a = (i * Math.PI) / 3 + 0.3; return at([cx + 11.6 * Math.cos(a), cy + 11.6 * Math.sin(a), OUTLET.lip]); }), { size: 0.5, tone: "mid" }));
  // The thermocouple on the metal: a boss on the scroll, a stem, a knurled head.
  const [px, py] = HOUSING_PROBE;
  out.push(S(k.cylinder(px, py, 2.8, z1, 2.2, P, 24), { tone: "mid" }));
  out.push(S(k.cylinder(px, py, 1.0, z1 + 2.2, 4, P, 12), { tone: "hi", crease: "none" }));
  out.push(S(k.cylinder(px, py, 2.4, z1 + 6.2, 5, P, 24), { tone: "mid" }));
  out.push(L(k.knurl(px, py, 2.4, z1 + 6.2, z1 + 11.2, 20, P), { tone: "lo" }));
  return out.join("");
}

// ---- the recorder ---------------------------------------------------------------------------
const faceAt = (u, v) => at([PAPER.x0 + u, FACE, PAPER.z0 + v]);
const PW = PAPER.x1 - PAPER.x0;
const PH = PAPER.z1 - PAPER.z0;

function recorder() {
  const out = [];
  out.push(S(k.slabOf(k.insetPlan(RECORDER, -1.2), 0, 4, P, 4, 0.5), { tone: "lo" }));
  out.push(S(k.slabOf(RECORDER, 4, RECORDER_TOP - 4, P, 4, 1.2), { tone: "mid", inner: L(k.sideSeam(RECORDER, RECORDER_TOP - 3.5, P, 4), { tone: "faint" }) }));
  // Top: two knurled range knobs and a label plate.
  for (const [x, y] of [[RECORDER.x + 16, RECORDER.y + 14], [RECORDER.x + 30, RECORDER.y + 14]]) {
    out.push(S(k.cylinder(x, y, 4.2, RECORDER_TOP, 4.4, P, 32), { tone: "mid" }));
    out.push(L(k.knurl(x, y, 4.2, RECORDER_TOP, RECORDER_TOP + 4.4, 32, P), { tone: "lo" }));
    out.push(L(k.lineOnTop([x, y], [x + 3.4, y + 1.4], RECORDER_TOP + 4.4, P), { tone: "hi" }));
  }
  const label = { x: RECORDER.x + 72, y: RECORDER.y + 8, w: 56, d: 16, r: 1.5 };
  out.push(S(k.slabOf(label, RECORDER_TOP, 0.8, P, 3), { tone: "lo", crease: "none" }));
  out.push(L(k.planOutline(k.insetPlan(label, 1.6), RECORDER_TOP + 0.8, P, 3), { tone: "faint" }));
  for (const [y, w] of [[4.6, 34], [8, 26], [11.4, 30]]) out.push(L(k.lineOnTop([label.x + 5, label.y + y], [label.x + 5 + w, label.y + y], RECORDER_TOP + 0.8, P), { tone: "lo", free: true }));
  // Front: the bezel, the paper and its fixed grid.
  out.push(L(faceRect(FACE, PAPER.x0 - 3, PAPER.x1 + 3, PAPER.z0 - 3, PAPER.z1 + 3), { tone: "lo" }));
  out.push(D([[PAPER.x0 - 1.6, PAPER.z0 - 1.6], [PAPER.x1 + 1.6, PAPER.z0 - 1.6], [PAPER.x0 - 1.6, PAPER.z1 + 1.6], [PAPER.x1 + 1.6, PAPER.z1 + 1.6]].map(([x, z]) => at([x, FACE, z])), { size: 0.42 }));
  out.push(`<path class="hl-paper" d="${faceRect(FACE, PAPER.x0, PAPER.x1, PAPER.z0, PAPER.z1)}"/>`);
  const level = (c) => (c / T_TOP) * PH;
  out.push(L([200, 400, 600, 800].map((c) => k.pathOf([faceAt(0, level(c)), faceAt(PW, level(c))])).join(""), { tone: "faint" }));
  out.push(`<path class="iso-line" data-tone="faint" data-part="grid" d=""/>`);
  // Ticks hang from the paper's left edge into the bezel, every 100 °C.
  const minor = [];
  const major = [];
  for (let c = 0; c <= T_TOP; c += 100) {
    const v = level(c);
    (c % 500 === 0 ? major : minor).push(k.pathOf([faceAt(0, v), at([PAPER.x0 - (c % 500 === 0 ? 2.6 : 1.6), FACE, PAPER.z0 + v])]));
  }
  out.push(L(minor.join(""), { tone: "lo" }), L(major.join(""), { tone: "mid" }));
  out.push(`<path class="iso-line" data-tone="mid" data-dashed="" data-free="start" data-part="gas-trace" d=""/>`);
  out.push(`<path class="iso-line hl-trace" data-tone="lit" data-free="start" data-part="housing-trace" d=""/>`);
  out.push(`<g data-part="tau" style="display:none"><path class="iso-line" data-tone="mid" data-part="tau-line" d=""/><circle class="hl-tau" data-part="tau-dot" r="1.5" cx="0" cy="0"/></g>`);
  out.push(L(faceRect(FACE, PAPER.x0, PAPER.x1, PAPER.z0, PAPER.z1), { tone: "mid" }));
  // The binding posts where the two thermocouple leads land.
  for (const x of [POSTS.gas, POSTS.housing]) {
    out.push(S(k.slabOf({ x: x - 2.4, y: FACE, w: 4.8, d: 3.4, r: 0.9 }, 7, 5.6, P, 3, 0.4), { tone: "mid" }));
  }
  return out.join("");
}

// One pen: brackets on the face, a vertical rod, and a carriage whose arm
// reaches the paper's right edge. The carriage is built at z = 0 and moved.
function rod({ x, y }) {
  const out = [];
  for (const z of [PAPER.z0 - 5, PAPER.z1 + 2]) out.push(S(k.slabOf({ x: x - 1.6, y: FACE, w: 3.2, d: y - FACE + 1.8, r: 0.6 }, z, 3, P, 2, 0.3), { tone: "mid" }));
  out.push(S(k.cylinder(x, y, 0.9, PAPER.z0 - 2, PH + 4, P, 12), { tone: "hi", crease: "none" }));
  return out.join("");
}
function pen({ x, y }, tone) {
  return [
    L(k.pathOf([at([x - 2.2, y, 0]), at([PAPER.x1, FACE, 0])]), { tone: tone === "lit" ? "lit" : "mid" }),
    S(k.slabOf({ x: x - 2.2, y: y - 2.2, w: 4.4, d: 4.4, r: 0.9 }, -2, 4, P, 2, 0.3), { tone: tone === "lit" ? "hi" : "mid", lit: tone === "lit" }),
    D([at([PAPER.x1, FACE, 0])], { size: 0.7, tone: "hi" }),
  ].join("");
}

// ---- the thermocouple leads --------------------------------------------------------------------
function smooth(points, rounds = 3) {
  let list = points;
  for (let round = 0; round < rounds; round++) {
    const next = [list[0]];
    for (let i = 0; i < list.length - 1; i++) {
      const [a, b] = [list[i], list[i + 1]];
      next.push(a.map((value, axis) => value * 0.75 + b[axis] * 0.25), a.map((value, axis) => value * 0.25 + b[axis] * 0.75));
    }
    next.push(list[list.length - 1]);
    list = next;
  }
  return list;
}
function lead(points) {
  const flat = smooth(points).map(at);
  return k.wireSvg(flat[0], flat[flat.length - 1], { via: flat.slice(1, -1), tone: "mid", size: 1 });
}
function leads() {
  const [gx, gy] = GAS_PROBE;
  const [hx, hy] = HOUSING_PROBE;
  const lane = 1.1;
  return [
    lead([[gx, gy, DUCT.z1 + 16], [gx, gy + 6, DUCT.z1 + 19], [gx, gy + 22, DUCT.z1 + 11], [gx, 34, 20], [gx + 1, 48, 5], [gx + 4, 52, lane], [POSTS.gas - 14, 52, lane], [POSTS.gas, 47, 3], [POSTS.gas, FACE + 3.4, 9.8]]),
    lead([[hx, hy, HOUSING.z1 + 11.2], [hx, hy + 6, HOUSING.z1 + 13], [hx, hy + 16, HOUSING.z1 + 2], [hx + 1, 52, 16], [hx + 3, 58, 3], [hx + 7, 59, lane], [POSTS.housing - 12, 59, lane], [POSTS.housing, 50, 3], [POSTS.housing, FACE + 3.4, 9.8]]),
  ].join("");
}

// ---- the page ------------------------------------------------------------------------------------
const svg = k.figureSvg({
  width: WIDTH,
  height: HEIGHT,
  label: COPY.ar.label,
  body: [
    plate(),
    burner(),
    `<g data-part="knob">${knob()}</g>`,
    duct(),
    housing(),
    recorder(),
    rod(RODS.gas),
    `<g data-part="pen-gas">${pen(RODS.gas, "mid")}</g>`,
    rod(RODS.housing),
    `<g data-part="pen-housing">${pen(RODS.housing, "lit")}</g>`,
    leads(),
  ],
});

const CSS = `
.iso-page{width:min(760px,100%);margin:0 auto;padding:8px}
.iso-figure{margin:0}
.iso-stage{cursor:pointer;touch-action:pan-y;border-radius:2px}
.iso-stage:focus-visible{outline:1px solid var(--anatomy-muted);outline-offset:6px}
.iso-svg{direction:ltr}
.iso{--hl-paper:#1c1c1a;--hl-flame:#ff7a2e;--hl-heat:#e8401c;--hl-void:#050505;--hl-lamp:#ffb23e}
.iso[data-theme="light"]{--hl-paper:#fffdf6;--hl-flame:#f06a1d;--hl-heat:#e2401a;--hl-void:#3c3c40;--hl-lamp:#f29a1d}
.hl-paper{fill:var(--hl-paper);stroke:none}
.hl-void{fill:var(--hl-void);stroke:none}
.hl-flame{fill:var(--hl-flame);stroke:none;opacity:0}
.hl-lamp{fill:var(--hl-lamp);stroke:none;opacity:0}
.hl-glow{fill:var(--hl-heat);stroke:none;opacity:0;mix-blend-mode:screen;pointer-events:none}
.iso[data-theme="light"] .hl-glow{mix-blend-mode:multiply}
.hl-trace{stroke-width:1.1}
.hl-tau{fill:var(--anatomy-paper);stroke:var(--anatomy-lit);stroke-width:.8}
.hl-hub{fill:var(--anatomy-shade-1);stroke:var(--anatomy-mid);stroke-width:.6}
.iso-caption bdi,.iso-plate-corner bdi{unicode-bidi:isolate}
[dir="rtl"] .iso-plate-corner,[dir="rtl"] .iso-legend{font-family:"Segoe UI",Tahoma,Arial,sans-serif;letter-spacing:0;text-transform:none}
[dir="rtl"] .iso-plate-corner[data-corner="fig"]{left:auto;right:0}
[dir="rtl"] .iso-plate-corner[data-corner="title"]{right:auto;left:0}
[dir="rtl"] .iso-plate-corner[data-corner="hint"]{left:auto;right:0}
[dir="rtl"] .iso-plate-corner[data-corner="readout"]{right:auto;left:0}
.iso-plate-corner bdi{font-family:var(--anatomy-mono)}
`;

const card = `<figure class="iso-figure"><div class="iso-plate"><div class="iso-plate-corners" aria-hidden="true"><span class="iso-plate-corner" data-corner="fig" data-text="fig"></span><span class="iso-plate-corner" data-corner="title" data-text="title"></span><span class="iso-plate-corner" data-corner="hint" data-text="hint"></span><span class="iso-plate-corner" data-corner="readout" data-readout><span data-read="phase"></span> · <span data-read="gas-word"></span> <bdi data-read="gas"></bdi> · <span data-read="housing-word"></span> <bdi data-read="housing"></bdi> · <bdi data-read="tau"></bdi></span></div><div class="iso-stage" tabindex="0" role="switch" aria-checked="false">${svg}</div></div><figcaption class="iso-legend"><span class="iso-keys"><span class="iso-key"><svg class="iso-swatch" data-mark="lit" viewBox="0 0 16 10" aria-hidden="true"><path d="M1.5 5h13"/></svg><span data-text="key0"></span></span><span class="iso-key"><svg class="iso-swatch" data-mark="dashed" viewBox="0 0 16 10" aria-hidden="true"><path d="M1.5 5h13"/></svg><span data-text="key1"></span></span><span class="iso-key"><svg class="iso-swatch" data-mark="dotted" viewBox="0 0 16 10" aria-hidden="true"><path d="M1.5 5h13"/></svg><span data-text="key2"></span></span></span><span class="iso-caption" data-html="caption"></span></figcaption></figure>`;

const { reference, ...lean } = PARAMS;
const live = `
const P = ${JSON.stringify(P)};
const PARAMS = ${JSON.stringify(lean)};
const COPY = ${JSON.stringify(COPY)};
const SPEED = ${SPEED}, SPAN = ${SPAN}, T_TOP = ${T_TOP};
const PAPER = ${JSON.stringify(PAPER)}, FACE = ${FACE}, PW = ${PW}, PH = ${PH};
const KNOB = ${JSON.stringify(KNOB)};
const WHEEL = ${JSON.stringify(WHEEL)};
${bladesAt.toString().replaceAll("k.iso", "iso").replaceAll("k.pathOf", "pathOf")}
const SETTLE_ON = ${SETTLE_ON};
${inline(join(LAB, "src", "model", "housing-lag.mjs"))}

const query = new URLSearchParams(location.search);
let saved = {};
try { saved = JSON.parse(localStorage.getItem("supra-lab-preferences")) || {}; } catch {}
const lang = (query.get("lang") || saved.language) === "en" ? "en" : "ar";
const theme = (query.get("theme") || saved.theme) === "light" ? "light" : "dark";
document.documentElement.lang = lang;
document.documentElement.dir = lang === "ar" ? "rtl" : "ltr";
document.body.dataset.theme = theme;
document.documentElement.style.colorScheme = theme;
if (parent !== window) document.body.style.background = "transparent";
const C = COPY[lang];
const touch = matchMedia("(pointer: coarse)").matches;
const words = { fig: C.fig, title: C.title, hint: touch ? C.hintTouch : C.hint, key0: C.keys[0], key1: C.keys[1], key2: C.keys[2] };
document.querySelectorAll("[data-text]").forEach((node) => { node.textContent = words[node.dataset.text]; });
document.querySelector('[data-html="caption"]').innerHTML = C.caption;
document.title = C.title;

const stage = document.querySelector(".iso-stage");
const svg = stage.querySelector("svg");
svg.setAttribute("aria-label", C.label);
stage.setAttribute("aria-label", C.stage);
const part = (name) => svg.querySelector('[data-part="' + name + '"]');
const read = (name) => document.querySelector('[data-read="' + name + '"]');
const el = { blades: part("blades"), knob: part("knob"), flame: part("flame"), lamp: part("lamp"), glow: part("glow"), grid: part("grid"), gas: part("gas-trace"), housing: part("housing-trace"), tau: part("tau"), tauLine: part("tau-line"), tauDot: part("tau-dot"), penGas: part("pen-gas"), penHousing: part("pen-housing") };
read("gas-word").textContent = C.gas;
read("housing-word").textContent = C.housing;

const turbine = PARAMS.turbine;
const LIT = inputsOf(PARAMS, true), OFF = inputsOf(PARAMS, false);
let lit = false, house = OFF.tAmbK, tenths = 0, carry = 0, samples = [], steps = [];
const now = () => tenths / 10;
const gasC = () => (lit ? LIT.egtK : OFF.egtK) - 273.15;
const record = () => { samples.push([now(), gasC(), house - 273.15]); const from = now() - SPAN - 20; while (samples.length > 2 && samples[1][0] < from) samples.shift(); };
function restart() { lit = false; house = OFF.tAmbK; tenths = 0; carry = 0; samples = []; steps = []; record(); }
function advance(seconds) {
  carry += seconds;
  while (carry >= 0.1 - 1e-9) {
    const input = lit ? LIT : OFF;
    house = stepHousing(turbine, house, 0.1, input.mdotExhGps, input.egtK, input.tAmbK);
    tenths += 1; carry -= 0.1;
    if (tenths % 10 === 0) record();
  }
}
function toggle() {
  record();
  lit = !lit;
  record();
  const input = lit ? LIT : OFF;
  steps.push({ t: now(), tau: tauOf(turbine, input.mdotExhGps) });
  if (steps.length > 12) steps.shift();
  stage.setAttribute("aria-checked", String(lit));
}
restart();

const clamp = (value, low, high) => Math.min(high, Math.max(low, value));
const level = (c) => clamp(c / T_TOP, 0, 1) * PH;
const faceAt = (u, v) => iso([PAPER.x0 + u, FACE, PAPER.z0 + v], P);
const uOf = (t) => PW - ((now() - t) / SPAN) * PW;
function houseAt(t) {
  for (let i = samples.length - 1; i > 0; i--) {
    const [t1, , c1] = samples[i], [t0, , c0] = samples[i - 1];
    if (t0 <= t && t <= t1) return t1 === t0 ? c1 : c0 + ((c1 - c0) * (t - t0)) / (t1 - t0);
  }
  return null;
}
function trace(index) {
  const start = now() - SPAN;
  const points = [];
  for (let i = 0; i < samples.length; i++) {
    const [t] = samples[i];
    if (t < start) continue;
    if (!points.length && i > 0) {
      const [t0, ...a] = samples[i - 1], b = samples[i];
      const share = (start - t0) / (t - t0 || 1);
      points.push(faceAt(0, level(a[index - 1] + (b[index] - a[index - 1]) * share)));
    }
    points.push(faceAt(uOf(t), level(samples[i][index])));
  }
  return pathOf(points);
}
let knobAt = 0, flameAt = 0, spin = 0, turn = 0;
const ease = (current, target, dt, seconds) => current + (target - current) * (1 - Math.exp(-dt / seconds));
const smoothstep = (a, b, x) => { const t = clamp((x - a) / (b - a), 0, 1); return t * t * (3 - 2 * t); };
function draw(dt) {
  const calm = dt === null;
  knobAt = calm ? (lit ? 1 : 0) : ease(knobAt, lit ? 1 : 0, dt, 0.16);
  flameAt = calm ? (lit ? 1 : 0) : ease(flameAt, lit ? 1 : 0, dt, 0.12);
  el.knob.setAttribute("transform", translateAlong(P, [knobAt * (KNOB.on - KNOB.off), 0, 0]));
  // The wheel turns only to show that gas flows; its speed is not computed.
  if (!calm) { spin = ease(spin, lit ? 5 : 0, dt, lit ? 0.8 : 2.4); turn += spin * dt; el.blades.setAttribute("d", bladesAt(turn)); }
  el.flame.style.opacity = (0.85 * flameAt).toFixed(3);
  el.lamp.style.opacity = flameAt.toFixed(3);
  const c = house - 273.15;
  // Hot iron starts to show a dull red somewhere past 500 °C; the tint only says "hotter".
  el.glow.style.opacity = (0.42 * smoothstep(520, SETTLE_ON + 40, c)).toFixed(3);
  el.gas.setAttribute("d", trace(1));
  el.housing.setAttribute("d", trace(2));
  const lines = [];
  for (let t = Math.ceil((now() - SPAN) / 50) * 50; t <= now(); t += 50) { const u = uOf(t); if (u > 0.2 && u < PW - 0.2) lines.push(pathOf([faceAt(u, 0), faceAt(u, PH)])); }
  el.grid.setAttribute("d", lines.join(""));
  el.penGas.setAttribute("transform", translateAlong(P, [0, 0, PAPER.z0 + level(gasC())]));
  el.penHousing.setAttribute("transform", translateAlong(P, [0, 0, PAPER.z0 + level(c)]));
  // tau: the latest step whose tau has run out before the next step began.
  let shown = null;
  for (let i = steps.length - 1; i >= 0; i--) {
    const step = steps[i], next = steps[i + 1];
    if (now() >= step.t + step.tau && (!next || next.t >= step.t + step.tau)) { shown = step; break; }
  }
  if (shown && shown.t >= now() - SPAN) {
    const end = shown.t + shown.tau, value = houseAt(end);
    const v = level(value), a = faceAt(uOf(shown.t), v), b = faceAt(uOf(end), v);
    el.tauLine.setAttribute("d", pathOf([a, b]));
    el.tauDot.setAttribute("cx", b[0].toFixed(1));
    el.tauDot.setAttribute("cy", b[1].toFixed(1));
    el.tau.style.display = "";
  } else el.tau.style.display = "none";
  const phase = lit ? "heating" : c > OFF.tAmbK - 273.15 + 5 ? "cooling" : "cold";
  read("phase").textContent = C.phase[phase];
  read("gas").textContent = Math.round(gasC()) + " °C";
  read("housing").textContent = Math.round(c) + " °C";
  read("tau").textContent = "τ " + Math.round(tauOf(turbine, (lit ? LIT : OFF).mdotExhGps)) + " " + C.seconds;
}

const still = matchMedia("(prefers-reduced-motion: reduce)");
let frame = 0, last = 0, visible = false, touring = !still.matches, tourClock = 0, wait = 1.4;
function tick(stamp) {
  const dt = last ? Math.min((stamp - last) / 1000, 1 / 30) : 1 / 60;
  last = stamp;
  if (wait > 0) wait -= dt;
  else {
    const model = dt * SPEED;
    if (touring) {
      tourClock += model;
      const phase = tourClock % 500;
      if ((phase >= 10 && phase < 150) !== lit) toggle();
    }
    advance(model);
  }
  draw(dt);
  frame = visible && !still.matches ? requestAnimationFrame(tick) : 0;
}
const run = () => { if (!frame && visible && !still.matches) { last = 0; frame = requestAnimationFrame(tick); } };
function act(kind) {
  touring = false;
  wait = 0;
  if (kind === "restart") restart(); else toggle();
  if (still.matches) { advance(200); draw(null); } else run();
}
new IntersectionObserver((entries) => { visible = entries[entries.length - 1].isIntersecting; if (visible) run(); }, { rootMargin: "120px 0px" }).observe(stage);
stage.addEventListener("click", () => act("toggle"));
stage.addEventListener("keydown", (event) => {
  if (event.key === " " || event.key === "Enter") { event.preventDefault(); act("toggle"); }
  if (event.key === "r" || event.key === "R") { event.preventDefault(); act("restart"); }
});
draw(null);

const tell = () => { if (parent !== window) parent.postMessage({ type: "supra-figure-height", id: "housing-lag", height: Math.ceil(document.documentElement.getBoundingClientRect().height) }, location.origin); };
new ResizeObserver(tell).observe(document.body);
tell();
`;

const page = k
  .pageHtml({ title: COPY.ar.title, theme: "dark", body: card, script: inline(join(HERE, "..", "kit", "iso-kit.mjs")) + live, width: 760 })
  .replace("</style>", `${CSS}</style>`)
  .replace('<html lang="en">', '<html lang="ar" dir="rtl">');

mkdirSync(dirname(OUT), { recursive: true });
writeFileSync(OUT, page);
console.log(`wrote ${OUT.slice(LAB.length + 1)}: tau on ${TAU_ON.toFixed(2)} s, tau off ${TAU_OFF.toFixed(1)} s, settles at ${SETTLE_ON.toFixed(1)} C, ${(page.length / 1024).toFixed(0)} KB`);
