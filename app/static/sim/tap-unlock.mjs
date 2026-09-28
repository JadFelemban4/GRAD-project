// The hidden gesture of /agents (M3 design 7.7): ten taps within four seconds
// on the footer label '02 — AGENTS' show the models panel.
//
// PURE: a counter and nothing else. agents.mjs passes each click's time in
// milliseconds; this module never reads a clock of its own. The taps live in
// this closure only, so a reload forgets them and the unlock, and nothing is
// kept in any browser store (tap-unlock.test.mjs reads this source to check).
// The gesture hides the panel; it protects nothing.
export function createTapUnlock({ taps = 10, windowMs = 4000 } = {}) {
  let times = [];
  return {
    // True on the tap that completes `taps` taps within `windowMs`; the count
    // then starts again from zero.
    tap(nowMs) {
      times.push(nowMs);
      times = times.filter(t => nowMs - t <= windowMs);
      if (times.length < taps) return false;
      times = [];
      return true;
    },
  };
}
