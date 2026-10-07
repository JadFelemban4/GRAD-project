/**
 * Illustration scale: how many replay metres one world unit stands for.
 *
 * It was 90, and at that scale SPEED WAS UNREADABLE. Measured on the shipped
 * camera (orthographic, 54 units across): 60 km/h crossed the view in 292 s
 * and 164 km/h in 107 s. The 2.7x ratio was there and neither looked like
 * motion, so a slow cruise and a hard pull were indistinguishable on screen.
 *
 * At 35 the same two speeds cross in 113 s and 41 s. Nothing about the data
 * changed -- this is a viewing scale, exactly like the zoom control, and it
 * enters no calculation: replay distance is integrated from recorded speed in
 * metres, and only the last step divides by this to place the car.
 *
 * The honest cost, and it is why the lap counter exists: the loop is now about
 * 4.6 km instead of 11.8, so a long drive laps it more often. The caption on
 * the scene names the lap and the loop length, so the repetition stays visible
 * rather than reading as a longer road than was driven.
 *
 * Lower bound: scene.test.mjs requires a 1 km preview to stay under a quarter
 * of the loop, which needs a value above about 30.
 */
export const METERS_PER_WORLD_UNIT = 35;
const TAU = Math.PI * 2;
const wrap = (v, length) => ((v % length) + length) % length;
const smooth = (a, b, v) => {
  const t = Math.max(0, Math.min(1, (v - a) / (b - a)));
  return t * t * (3 - 2 * t);
};
export function roadHeight(u) {
  u = wrap(u, 1);
  return 0.24 + 4.1 * smooth(0.19, 0.4, u) * (1 - smooth(0.56, 0.81, u));
}
function point(u) {
  return [25 * Math.sin(u * TAU), roadHeight(u), 16 * Math.cos(u * TAU)];
}
export function createRoad() {
  const count = 4096;
  const distances = new Float64Array(count + 1);
  let previous = point(0);
  for (let i = 1; i <= count; i++) {
    const p = point(i / count);
    distances[i] = distances[i - 1] + Math.hypot(...p.map((v, j) => v - previous[j]));
    previous = p;
  }
  const length = distances[count];
  return {
    length,
    atDistance(distance) {
      const d = wrap(Number.isFinite(distance) ? distance : 0, length);
      let lo = 0;
      let hi = count;
      while (hi - lo > 1) {
        const mid = (hi + lo) >> 1;
        if (distances[mid] <= d) lo = mid;
        else hi = mid;
      }
      const u = (lo + (d - distances[lo]) / (distances[hi] - distances[lo])) / count;
      const a = point(u - 0.00001);
      const b = point(u + 0.00001);
      const direction = b.map((v, i) => v - a[i]);
      const norm = Math.hypot(...direction);
      return { position: point(u), tangent: direction.map(v => v / norm) };
    },
  };
}
export function previewWorldLength(meters, loopLength) {
  return Number.isFinite(meters) ? Math.max(0, Math.min(meters / METERS_PER_WORLD_UNIT, loopLength)) : 0;
}
