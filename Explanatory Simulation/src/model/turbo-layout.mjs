export const TURBO_CENTER = [0, 0.85, 0];

export const turboAnchors = {
  compressor: [0, 0.85, 0.44],
  'compressor-housing': [0, 0.85, 0.44],
  turbine: [0, 0.85, -0.44],
  'turbo-shaft': [0, 0.85, 0],
  'turbo-housing': [0, 0.85, 0],
};

/** Guide curves only; they illustrate the split gas paths, not CFD streamlines. */
export const turboFlowPaths = {
  airInlet: [[0, 0.85, 0.98], [0, 0.85, 0.8], [0, 0.85, 0.65], [0, 0.85, 0.54]],
  airCharge: [[0, 0.85, 0.54], [0.2, 0.85, 0.44], [0.43, 0.94, 0.44], [0.56, 1.05, 0.44], [0.72, 1.25, 0.44], [0.95, 1.5, 0.44]],
  exhaustInlet: [[-1.08, 1.5, -0.7], [-0.87, 1.38, -0.65], [-0.65, 1.18, -0.58], [-0.47, 1.03, -0.5], [0, 0.85, -0.44]],
  exhaustOutlet: [[0, 0.85, -0.53], [0, 0.85, -0.7], [0, 0.85, -0.84], [0, 0.85, -0.98]],
};

const nonnegativeFinite = (value) => typeof value === 'number' && Number.isFinite(value) && value >= 0;

/** Read the supplied model flows in g/s. Missing or invalid values stay unavailable. */
export function turboFlowData(frame) {
  const air = nonnegativeFinite(frame?.mdot_air) ? frame.mdot_air : null;
  const fuel = nonnegativeFinite(frame?.mdot_fuel) ? frame.mdot_fuel : null;
  const sum = air !== null && fuel !== null ? air + fuel : null;
  const exhaust = sum !== null && Number.isFinite(sum) ? sum : null;
  return { air, exhaust };
}

/** Convert a real mass-flow input to a bounded illustrative animation only. */
export function flowVisual(rate) {
  if (!nonnegativeFinite(rate)) return null;
  const t = Math.min(rate / 250, 1);
  return { speed: 0.25 + 0.65 * t, density: 0.6 + 1.1 * t };
}

export function turboHousingPosition(side, explode = 0) {
  const amount = typeof explode === 'number' && Number.isFinite(explode) ? Math.max(0, Math.min(1, explode)) : 0;
  const z = side === 'compressor' ? 0.44 + amount * 0.24 : -0.44 - amount * 0.24;
  return [0, 0.85, z];
}

/** Advance an illustrative angular phase by elapsed presentation time, never absolute-time rate. */
export function advanceTurboPhase(phase, elapsed, rate) {
  if (!Number.isFinite(elapsed) || elapsed <= 0 || !Number.isFinite(rate) || rate < 0) return phase;
  return (phase + Math.min(elapsed, 0.1) * rate) % (Math.PI * 2);
}
