// Pure presentation logic for /agents. No DOM, no Three.js, no fetch, and no
// physics: every number this module handles was computed in Python by
// app/agent_trace.py and arrived as JSON. It decides WHERE and WHEN to show a
// value, never what the value is, and it computes nothing that compares the two
// cars. That is why all of it can be tested under node without a browser.

// The scoring protocol's step (evaluate.py DT = 1.0). Frame k covers t = k..k+1.
export const DT = 1;
// Chase-view scale: metres per world unit, the SAME on both axes, so the slope
// on screen is the true slope (design section 5). Changing it alone would not
// exaggerate anything, but the caption «الميل غير مضخّم» depends on it being one
// number for x and z.
export const M_PER_UNIT = 10;
// The whole-route profile's vertical exaggeration; the page prints it (×3).
export const PROFILE_VE = 3;
// Preview marks are coloured on one hue from 0 to this grade, in percent.
export const GRADE_RAMP_MAX_PCT = 16;
// supra()'s bounding half-width in world units, measured on its geometry with
// the light pools left out: the wheel hub ring reaches 1.23 + 0.2 + 0.0563 =
// 1.486 (scene.mjs supra, a TorusGeometry with 6 radial segments). The design's
// "about 1.48" stopped at the spokes (1.4825); agent-scene.test.mjs re-measures.
export const CAR_HALF_WIDTH = 1.49;
// Lateral offset of each car from the road centre: + is the sighted lane, - the
// blind lane. ±1.9 leaves a gap of about 0.83 units between the two cars.
export const CAR_OFFSET = 1.9;
// Width of each lane tint, and of the whole road ribbon.
export const LANE_W = 3.2;
export const ROAD_W = 7.6;

// The five actions in engine_env order (ACT_LO / ACT_HI, engine_env.py:513-514).
// The labels are i18n keys from agents-strings.mjs; digits is display rounding.
export const ACTIONS = Object.freeze([
  Object.freeze({ key: 'spark', label: 'agents.action.spark', unit: '°', digits: 1 }),
  Object.freeze({ key: 'lambda', label: 'agents.action.lambda', unit: 'λ', digits: 3 }),
  Object.freeze({ key: 'boost', label: 'agents.action.boost', unit: 'kPa', digits: 1 }),
  Object.freeze({ key: 'fan', label: 'agents.action.fan', unit: '', digits: 2 }),
  Object.freeze({ key: 'pump', label: 'agents.action.pump', unit: '', digits: 2 }),
]);

const finite = Number.isFinite;
const clamp = (v, lo, hi) => Math.min(hi, Math.max(lo, v));
// Exact at both ends: a + 1 * (b - a) is not always b in floating point.
const lerp = (a, b, u) => (u === 0 ? a : u === 1 ? b : a + u * (b - a));

// Index of the last vertex at or before `value` in an ascending array
// (-1 when value is below the first vertex).
function lastAtOrBefore(values, value) {
  let lo = 0;
  let hi = values.length;
  while (lo < hi) {
    const mid = (lo + hi) >>> 1;
    if (values[mid] <= value) lo = mid + 1; else hi = mid;
  }
  return lo - 1;
}

/**
 * The episode road in the shape scene.mjs's ribbonGeometry() walks:
 * { length, atDistance(d) -> { position: [x, y, z], tangent: [x, y, z] } }.
 *
 * World X is distance along the (straight) route, world Y is elevation, world Z
 * is across the road; all in world units of `mPerUnit` metres. Positions are
 * linear between the route's own vertices, so they are EXACT at every vertex,
 * and the tangent is the unit vector of the segment the point lies on. The first
 * segment of every episode has zero length (the launch starts at v = 0, so
 * s[0] == s[1]); a zero-length segment never supplies a tangent.
 */
export function createEpisodeRoad(road, mPerUnit = M_PER_UNIT) {
  const s = road.s_m.map(v => v / mPerUnit);
  const x = road.x_m.map(v => v / mPerUnit);
  const z = road.z_m.map(v => v / mPerUnit);
  const last = s.length - 1;
  const length = s[last];
  const atDistance = d => {
    if (last < 1) return { position: [x[0], z[0], 0], tangent: [1, 0, 0] };
    const dd = clamp(finite(d) ? d : 0, 0, length);
    let i = clamp(lastAtOrBefore(s, dd), 0, last - 1);
    while (i < last - 1 && s[i + 1] === s[i]) i += 1;   // onto a segment with length
    let t = i;
    while (t > 0 && s[t + 1] === s[t]) t -= 1;           // a tangent from one with length
    const span = s[i + 1] - s[i];
    const u = span > 0 ? clamp((dd - s[i]) / span, 0, 1) : 0;
    const dx = x[t + 1] - x[t];
    const dz = z[t + 1] - z[t];
    const n = Math.hypot(dx, dz);
    return {
      position: [lerp(x[i], x[i + 1], u), lerp(z[i], z[i + 1], u), 0],
      tangent: n > 0 ? [dx / n, dz / n, 0] : [1, 0, 0],
    };
  };
  return { length, mPerUnit, atDistance };
}

/**
 * Where both cars are at clock time t (seconds). The scenario imposes the speed
 * (engine_env.py:729), so the two cars share one s. Within a step the env holds
 * speed constant, so s, x and z are linear between vertex k and k + 1: exact.
 *
 * t is clamped to [0, frames.length] -- the computed end -- and k to the last
 * computed frame. With no frames, k is -1 and frame is null.
 */
export function episodeAt(frames, road, t) {
  const n = frames.length;
  const tt = clamp(finite(t) ? t : 0, 0, n);
  const k = n ? Math.min(Math.floor(tt), n - 1) : -1;
  const frame = k >= 0 ? frames[k] : null;
  if (!road) return { k, frame, s_m: null, x_m: null, z_m: null, t: tt };
  const i = Math.max(0, k);
  const j = Math.min(i + 1, road.s_m.length - 1);
  const u = k >= 0 ? tt - k : 0;
  const at = a => lerp(a[i], a[j], u);
  return { k, frame, s_m: at(road.s_m), x_m: at(road.x_m), z_m: at(road.z_m), t: tt };
}

/**
 * The whole-route side profile as points in a y-UP box `width` wide. x is
 * scaled to fit; y is the same scale times `ve`, so the exaggeration applies to
 * elevation only. The caller flips y for SVG (svgY = height - y).
 */
export function profilePoints(road, { ve = PROFILE_VE, width = 1000 } = {}) {
  const x0 = road.x_m[0];
  const span = road.x_m[road.x_m.length - 1] - x0;
  const zMin = Math.min(...road.z_m);
  const zMax = Math.max(...road.z_m);
  const sx = span > 0 ? width / span : 0;
  const points = road.x_m.map((x, i) => [(x - x0) * sx, (road.z_m[i] - zMin) * sx * ve]);
  return { points, width, height: (zMax - zMin) * sx * ve, ve, sx };
}

/**
 * The road positions the sighted agent's four preview inputs describe at step
 * k: engine_env._preview() reads the grade at min(k + int(h / dt), len - 1).
 * Math.trunc is Python's int() for these non-negative horizons.
 */
export function previewMarks(road, k, previewS, dt = DT) {
  const last = road.s_m.length - 1;
  return previewS.map(h => {
    const index = Math.min(Math.max(0, k) + Math.trunc(h / dt), last);
    return { h, index, s_m: road.s_m[index], x_m: road.x_m[index], z_m: road.z_m[index], grade_pct: road.grade_pct[index] };
  });
}

/** Position of v on a bar from lo to hi, clamped to [0, 1]; null when unknown. */
export function gaugeFraction(v, lo, hi) {
  if (![v, lo, hi].every(finite) || hi <= lo) return null;
  return clamp((v - lo) / (hi - lo), 0, 1);
}

/**
 * The network's command in physical units, as engine_env._rescale does it
 * (lo + (clip(a, -1, 1) + 1) / 2 * (hi - lo)). For DISPLAY of a held command
 * only: this is float64 where the env is float32, and the applied value always
 * comes from the frame, never from here.
 */
export function commandPhysical(cmd, lo, hi) {
  return cmd.map((a, i) => (finite(a) && finite(lo[i]) && finite(hi[i])
    ? lo[i] + (clamp(a, -1, 1) + 1) / 2 * (hi[i] - lo[i])
    : null));
}

/** 0 at a flat road, 1 at GRADE_RAMP_MAX_PCT and steeper; null when unknown. */
export function gradeRamp(pct) {
  return finite(pct) ? clamp(pct / GRADE_RAMP_MAX_PCT, 0, 1) : null;
}

// ---------------------------------------------------------------- playback
// PlaybackClock.play() rewinds to 0 when time >= duration (playback.mjs:9).
// While the episode is still being computed, the clock's duration is the
// COMPUTED end, so a play pressed there must wait for frames instead.

/** userPaused starts true: nothing plays until the viewer presses play. */
export function createPlayState(clock) {
  return { clock, waiting: false, userPaused: true };
}

/**
 * The play button. Returns true when it is now WAITING for frames. It never
 * calls clock.play() at the computed edge of an unfinished build, because that
 * would rewind to 0.
 */
export function playOrWait(state, computedEnd, done, now) {
  const { clock } = state;
  clock.tick(now);
  clock.duration = Math.max(0, computedEnd);
  state.userPaused = false;
  if (!done && clock.time >= clock.duration) {
    clock.pause(now);
    state.waiting = true;
    return true;
  }
  state.waiting = false;
  clock.play(now);
  return false;
}

/** The pause button: the viewer's own stop, which no frame arrival undoes. */
export function pauseByUser(state, now) {
  state.clock.pause(now);
  state.userPaused = true;
  state.waiting = false;
}

/**
 * Frames arrived: the computed end moved to newEnd. Always extends the clock's
 * duration. Resumes playback only if the viewer did not pause and the clock had
 * stopped at the old edge or was waiting. Returns true when it resumed.
 */
export function resumeIfStalled(state, newEnd, now) {
  const { clock } = state;
  clock.tick(now);
  const stalled = state.waiting || (!clock.playing && clock.time >= clock.duration);
  clock.duration = Math.max(clock.duration, newEnd);
  if (state.userPaused || !stalled || clock.time >= clock.duration) return false;
  state.waiting = false;
  clock.play(now);
  return true;
}

/**
 * The build finished ('ready'). Fixes the clock's duration at `end` and clears
 * a wait that no new frame will ever release. Returns whether it was waiting,
 * so the caller can turn the button back to play; the next play then behaves
 * like the lab's (it rewinds from the end).
 */
export function settleDone(state, end, now) {
  const { clock } = state;
  clock.tick(now);
  clock.duration = Math.max(0, end);
  const was = state.waiting;
  state.waiting = false;
  return was;
}

// ---------------------------------------------------------------- polling

/**
 * Append one poll's slice of frames. Accepted only when it starts exactly at
 * the end of what is held (payload.since === frames.length) and every incoming
 * frame's k equals its index, so a stale, overlapping or gapped response can
 * never shift the clock onto another second's decision. Mutates only on
 * accept; an empty slice at the right since is accepted and changes nothing.
 */
export function appendFrames(frames, payload) {
  if (!payload || !Array.isArray(payload.frames) || payload.since !== frames.length) return false;
  const base = frames.length;
  if (!payload.frames.every((f, i) => f && f.k === base + i)) return false;
  frames.push(...payload.frames);
  return true;
}

/** Step at which a lane's car first went null (its simulation stopped), or null. */
export function laneStoppedAt(frames, lane) {
  const k = frames.findIndex(f => f && f.cars && f.cars[lane] == null);
  return k < 0 ? null : frames[k].k;
}
