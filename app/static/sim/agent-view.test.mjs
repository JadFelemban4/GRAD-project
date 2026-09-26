import test from 'node:test';
import assert from 'node:assert/strict';
import { PlaybackClock } from './playback.mjs';
import { STRINGS, LANGS } from './i18n.mjs';
import './agents-strings.mjs';
let V;
let loadError = null;
try { V = await import('./agent-view.mjs'); } catch (err) { loadError = err; }
const api = () => { assert.ok(V, `agent-view.mjs must load: ${loadError?.message}`); return V; };

// A short route built exactly as app/agent_trace.route() builds one (design
// section 5): ds_k = v_k * dt over the stepped samples, x += ds cos(atan g),
// z += ds sin(atan g). A launch from rest, flat running, then a 13.314 % climb.
const SPEED = [0, 10, 20, 30, 36.1, 36.1, 36.1, 36.1, 36.1, 36.1, 36.1, 36.1, 36.1, 36.1];
const GRADE = [0, 0, 0, 0, 0, 0, 0, 0.13314, 0.13314, 0.13314, 0.13314, 0.13314, 0.13314, 0.13314];
function makeRoad(v = SPEED, g = GRADE, dt = 1) {
  const s = [0], x = [0], z = [0];
  for (let k = 0; k < v.length - 1; k++) {
    const th = Math.atan(g[k]);
    const ds = v[k] * dt;
    s.push(s[k] + ds); x.push(x[k] + ds * Math.cos(th)); z.push(z[k] + ds * Math.sin(th));
  }
  return { s_m: s, x_m: x, z_m: z, grade_pct: g.map(u => u * 100), speed_kmh: v.map(u => u * 3.6) };
}
const road = makeRoad();
const LAST = road.s_m.length - 1;   // 13
const close = (a, b, tol, msg) => assert.ok(Math.abs(a - b) <= tol, `${msg}: ${a} vs ${b}`);

test('createEpisodeRoad is exact at every vertex, true to the slope, and clamped', () => {
  const { createEpisodeRoad, M_PER_UNIT } = api();
  const M = M_PER_UNIT;
  const r = createEpisodeRoad(road);
  assert.equal(r.mPerUnit, 10);
  assert.equal(r.length, road.s_m[LAST] / M);
  for (let k = 0; k <= LAST; k++) {
    const { position } = r.atDistance(road.s_m[k] / M);
    close(position[0], road.x_m[k] / M, 1e-12, `x at vertex ${k}`);
    close(position[1], road.z_m[k] / M, 1e-12, `z at vertex ${k}`);
    assert.equal(position[2], 0);
  }
  // On the climb the tangent's rise over run is the grade itself: the slope is not exaggerated.
  const onClimb = r.atDistance((road.s_m[9] + road.s_m[10]) / 2 / M).tangent;
  close(onClimb[1] / onClimb[0], 0.13314, 1e-12, 'rise over run on the climb');
  close(Math.hypot(...onClimb), 1, 1e-12, 'unit tangent');
  // s[0] == s[1] (launch from rest): the zero-length segment never yields a NaN tangent.
  assert.deepEqual(r.atDistance(0).tangent, [1, 0, 0]);
  assert.deepEqual(r.atDistance(-5), r.atDistance(0));
  assert.deepEqual(r.atDistance(NaN), r.atDistance(0));
  assert.deepEqual(r.atDistance(r.length + 50).position, [road.x_m[LAST] / M, road.z_m[LAST] / M, 0]);
  assert.deepEqual(createEpisodeRoad({ s_m: [0, 0], x_m: [0, 0], z_m: [0, 0] }).atDistance(0).tangent, [1, 0, 0]);
});

test('episodeAt is linear inside a step, clamped to the computed frames, and empty before any', () => {
  const { episodeAt } = api();
  const frames = [{ k: 0 }, { k: 1 }, { k: 2 }];
  const mid = episodeAt(frames, road, 1.25);
  assert.equal(mid.k, 1);
  assert.equal(mid.frame, frames[1]);
  close(mid.s_m, road.s_m[1] + 0.25 * (road.s_m[2] - road.s_m[1]), 1e-12, 's inside step 1');
  close(mid.z_m, road.z_m[1] + 0.25 * (road.z_m[2] - road.z_m[1]), 1e-12, 'z inside step 1');
  const past = episodeAt(frames, road, 99);   // three frames computed: the clock ends at t = 3
  assert.equal(past.t, 3);
  assert.equal(past.k, 2);
  assert.equal(past.s_m, road.s_m[3]);
  const before = episodeAt(frames, road, -4);
  assert.equal(before.t, 0);
  assert.equal(before.k, 0);
  assert.equal(before.s_m, road.s_m[0]);
  const none = episodeAt([], road, 5);
  assert.equal(none.k, -1);
  assert.equal(none.frame, null);
  assert.equal(none.s_m, road.s_m[0]);
  assert.equal(episodeAt(frames, null, 1).s_m, null);
});

test('profilePoints exaggerates elevation only; previewMarks stop at the last vertex', () => {
  const { profilePoints, previewMarks, PROFILE_VE } = api();
  assert.equal(PROFILE_VE, 3);
  const flat = profilePoints(road, { ve: 1, width: 500 });
  const tall = profilePoints(road, { width: 500 });
  assert.equal(tall.ve, 3);
  assert.equal(tall.points.length, road.x_m.length);
  close(tall.points[LAST][0], 500, 1e-9, 'x spans the width');
  close(tall.height, 3 * flat.height, 1e-9, 'height scales by ve');
  tall.points.forEach(([x, y], i) => {
    assert.equal(x, flat.points[i][0]);
    close(y, 3 * flat.points[i][1], 1e-9, `y at ${i}`);
  });
  // engine_env._preview(): min(k + int(h / dt), len - 1)
  const marks = previewMarks(road, 3, [2, 5, 15, 30]);
  assert.deepEqual(marks.map(m => m.index), [5, 8, 13, 13]);
  assert.deepEqual(marks.map(m => m.h), [2, 5, 15, 30]);
  assert.equal(marks[1].grade_pct, road.grade_pct[8]);
  assert.equal(marks[1].s_m, road.s_m[8]);
  assert.deepEqual(previewMarks(road, 0, [2], 0.2).map(m => m.index), [10]);
});

test('gauges, commands and the grade ramp', () => {
  const { gaugeFraction, commandPhysical, gradeRamp, GRADE_RAMP_MAX_PCT } = api();
  assert.equal(gaugeFraction(-8, -8, 4), 0);
  assert.equal(gaugeFraction(4, -8, 4), 1);
  assert.equal(gaugeFraction(0, -8, 4), 8 / 12);            // the spark «بلا تعديل» tick
  assert.equal(gaugeFraction(1, 0.3, 1), 1);                // pump at the baseline row's 1.0
  assert.equal(gaugeFraction(9, -8, 4), 1);
  for (const bad of [null, undefined, NaN, Infinity]) assert.equal(gaugeFraction(bad, 0, 1), null);
  assert.equal(gaugeFraction(0.5, 1, 1), null);
  const LO = [-8, -0.15, -40, 0, 0.3];
  const HI = [4, 0.06, 15, 1, 1];
  assert.deepEqual(commandPhysical([-1, -1, -1, -1, -1], LO, HI), LO);
  assert.deepEqual(commandPhysical([1, 1, 1, 1, 1], LO, HI), HI);
  assert.deepEqual(commandPhysical([-7, 7, 2, -2, 1], LO, HI), [-8, 0.06, 15, 0, 1]);
  const mid = commandPhysical([0, 0, 0, 0, 0], LO, HI);
  [-2, -0.045, -12.5, 0.5, 0.65].forEach((v, i) => close(mid[i], v, 1e-12, `midpoint ${i}`));
  assert.equal(commandPhysical([NaN, 0, 0, 0, 0], LO, HI)[0], null);
  // A diverged step reaches the page as five nulls (agent_trace.jsonable turns
  // NaN into None) with held all true: there is no command to show.
  assert.deepEqual(commandPhysical([null, null, null, null, null], LO, HI), [null, null, null, null, null]);
  assert.equal(GRADE_RAMP_MAX_PCT, 16);
  assert.equal(gradeRamp(0), 0);
  assert.equal(gradeRamp(8), 0.5);
  assert.equal(gradeRamp(16), 1);
  assert.equal(gradeRamp(21), 1);
  assert.equal(gradeRamp(-2), 0);
  assert.equal(gradeRamp(null), null);
});

test('the two cars and their lanes fit the road without touching', () => {
  const { CAR_OFFSET, CAR_HALF_WIDTH, LANE_W, ROAD_W, M_PER_UNIT, DT } = api();
  assert.equal(M_PER_UNIT, 10);
  assert.equal(DT, 1);
  assert.ok(2 * CAR_OFFSET > 2 * CAR_HALF_WIDTH, 'the cars overlap');
  assert.ok(LANE_W > 2 * CAR_HALF_WIDTH, 'a lane tint is narrower than its car');
  assert.ok(CAR_OFFSET + LANE_W / 2 <= ROAD_W / 2, 'a lane tint runs off the road');
  assert.ok(CAR_OFFSET - LANE_W / 2 >= 0, 'the two lane tints overlap');
});

test('ACTIONS lists the five actions in engine_env order, each with a label in both languages', () => {
  const { ACTIONS } = api();
  assert.equal(ACTIONS.length, 5);
  assert.deepEqual(ACTIONS.map(a => a.key), ['spark', 'lambda', 'boost', 'fan', 'pump']);
  for (const a of ACTIONS) {
    for (const lang of LANGS) assert.ok(STRINGS[lang][a.label], `${a.label} missing in ${lang}`);
  }
});

// ------------------------------------------------ playback at the computed edge
// PlaybackClock.play() rewinds to 0 at its end (playback.mjs:9). While the
// episode is still being computed, the clock's end is the COMPUTED end.

test('play at the computed edge waits instead of rewinding, and rewinds once done', () => {
  const { createPlayState, playOrWait } = api();
  const state = createPlayState(new PlaybackClock(0));
  assert.deepEqual({ waiting: state.waiting, userPaused: state.userPaused }, { waiting: false, userPaused: true });
  state.clock.duration = 5;
  state.clock.seek(5, 0);
  assert.equal(playOrWait(state, 5, false, 100), true);
  assert.equal(state.waiting, true);
  assert.equal(state.clock.time, 5, 'it rewound at the computed edge');
  assert.equal(state.clock.playing, false);
  assert.equal(playOrWait(state, 5, true, 200), false);   // the build is done: behave like the lab
  assert.equal(state.waiting, false);
  assert.equal(state.clock.time, 0);
  assert.equal(state.clock.playing, true);
  const inside = createPlayState(new PlaybackClock(0));
  inside.clock.duration = 5;
  inside.clock.seek(2, 0);
  assert.equal(playOrWait(inside, 5, false, 0), false);
  assert.equal(inside.clock.time, 2);
  assert.equal(inside.clock.playing, true);
});

test('new frames resume a wait or a stop at the edge, never a pause the viewer made', () => {
  const { createPlayState, playOrWait, pauseByUser, resumeIfStalled } = api();
  // (a) waiting after play at the edge
  const waiting = createPlayState(new PlaybackClock(0));
  playOrWait(waiting, 0, false, 0);                          // play pressed before any frame
  assert.equal(waiting.waiting, true);
  assert.equal(resumeIfStalled(waiting, 4, 300), true);
  assert.equal(waiting.clock.duration, 4);
  assert.equal(waiting.clock.playing, true);
  assert.equal(waiting.waiting, false);
  // (b) playback ran into the computed edge by itself
  const edge = createPlayState(new PlaybackClock(0));
  playOrWait(edge, 3, false, 0);
  assert.equal(edge.clock.tick(5000), 3);
  assert.equal(edge.clock.playing, false);
  assert.equal(resumeIfStalled(edge, 6, 5000), true);
  assert.equal(edge.clock.time, 3);
  assert.equal(edge.clock.playing, true);
  // (c) the viewer paused: the duration still grows, playback does not resume
  const paused = createPlayState(new PlaybackClock(0));
  playOrWait(paused, 10, false, 0);
  pauseByUser(paused, 1000);
  assert.equal(resumeIfStalled(paused, 20, 2000), false);
  assert.equal(paused.clock.duration, 20);
  assert.equal(paused.clock.playing, false);
  assert.equal(paused.clock.time, 1);
  paused.clock.seek(20, 2000);                               // paused AT the edge is still a pause
  assert.equal(resumeIfStalled(paused, 30, 2000), false);
  // (d) nothing was ever played: frames arriving start nothing
  const idle = createPlayState(new PlaybackClock(0));
  assert.equal(resumeIfStalled(idle, 7, 0), false);
  assert.equal(idle.clock.duration, 7);
  assert.equal(idle.clock.playing, false);
  // (e) playing well inside the computed part: keep playing, just extend
  const running = createPlayState(new PlaybackClock(0));
  playOrWait(running, 10, false, 0);
  assert.equal(resumeIfStalled(running, 12, 1000), false);
  assert.equal(running.clock.playing, true);
  assert.equal(running.clock.duration, 12);
});

test('settleDone releases a wait that a ready poll with no new frames would leave pending', () => {
  const { createPlayState, playOrWait, resumeIfStalled, settleDone } = api();
  const state = createPlayState(new PlaybackClock(0));
  playOrWait(state, 719, false, 0);
  state.clock.seek(719, 0);
  playOrWait(state, 719, false, 10);                         // pressed at the edge: waiting
  assert.equal(state.waiting, true);
  assert.equal(resumeIfStalled(state, 719, 20), false);      // 'ready' brought no new frame
  assert.equal(settleDone(state, 719, 30), true);
  assert.equal(state.waiting, false);
  assert.equal(state.clock.duration, 719);
  assert.equal(playOrWait(state, 719, true, 40), false);     // next play rewinds, as in the lab
  assert.equal(state.clock.time, 0);
  assert.equal(state.clock.playing, true);
  // a cached 'ready' delivering all 719 frames at once to a page waiting at 0
  const cached = createPlayState(new PlaybackClock(0));
  playOrWait(cached, 0, false, 0);
  assert.equal(resumeIfStalled(cached, 719, 5), true);
  assert.equal(settleDone(cached, 719, 5), false);
  assert.equal(cached.clock.playing, true);
});

// ------------------------------------------------------------------ polling

test('appendFrames takes only the slice that starts where the held frames end', () => {
  const { appendFrames } = api();
  const frames = [];
  assert.equal(appendFrames(frames, { since: 0, frames: [{ k: 0 }, { k: 1 }] }), true);
  const held = structuredClone(frames);
  assert.equal(appendFrames(frames, { since: 0, frames: [{ k: 0 }] }), false, 'stale since');
  assert.equal(appendFrames(frames, { since: 1, frames: [{ k: 1 }, { k: 2 }] }), false, 'overlap');
  assert.equal(appendFrames(frames, { since: 3, frames: [{ k: 3 }] }), false, 'gap');
  assert.equal(appendFrames(frames, { since: 2, frames: [{ k: 3 }] }), false, 'k does not match its index');
  assert.equal(appendFrames(frames, null), false);
  assert.equal(appendFrames(frames, { since: 2 }), false);
  assert.deepEqual(frames, held);
  assert.equal(appendFrames(frames, { since: 2, frames: [] }), true, 'an empty slice at the right since');
  assert.deepEqual(frames, held);
  assert.equal(appendFrames(frames, { since: 2, frames: [{ k: 2 }] }), true);
  assert.deepEqual(frames.map(f => f.k), [0, 1, 2]);
});

test('parseEpisodeQuery reads the M1 address and nothing else', () => {
  const { parseEpisodeQuery } = api();
  assert.deepEqual(parseEpisodeQuery('?runs=runs_c4&seed=5&ep=1'), { runs: 'runs_c4', seed: 5, ep: 1 });
  assert.deepEqual(parseEpisodeQuery('runs=runs&seed=0&ep=20'), { runs: 'runs', seed: 0, ep: 20 });
  // runs_C4 is refused as the server refuses it (agent_catalog.RUNS_NAME is
  // lowercase-only: on Windows it would alias runs_c4 with no verdict).
  for (const bad of ['?runs=runs_c4&seed=5abc&ep=1', '?runs=../x&seed=5&ep=1', '?runs=runs_c4/../runs&seed=5&ep=1',
    '?runs=runs_c4&seed=5&ep=0', '?runs=runs_c4&seed=5&ep=21', '?runs=runs_c4&seed=1234&ep=1', '?runs=runs_C4&seed=5&ep=1',
    '?runs=runs_c4&seed=5', '?seed=5&ep=1', '', undefined]) {
    assert.equal(parseEpisodeQuery(bad), null, String(bad));
  }
});

test('laneStoppedAt names the first step a car went null', () => {
  const { laneStoppedAt } = api();
  const car = { damage: 0 };
  const frames = [{ k: 0, cars: [car, car] }, { k: 1, cars: [car, null] }, { k: 2, cars: [car, null] }];
  assert.equal(laneStoppedAt(frames, 1), 1);
  assert.equal(laneStoppedAt(frames, 0), null);
  assert.equal(laneStoppedAt([], 0), null);
});
