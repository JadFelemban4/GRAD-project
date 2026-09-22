// Presentation time only. This module never calculates or calls engine physics.
export class PlaybackClock {
  constructor(duration) { this.duration = Math.max(0, duration); this.time = 0; this.rate = 1; this.playing = false; this.wall = null; }
  tick(now) {
    if (this.wall !== null && this.playing) this.time = Math.min(this.duration, this.time + Math.max(0, now - this.wall) * this.rate / 1000);
    this.wall = now;
    if (this.time >= this.duration) this.playing = false;
    return this.time;
  }
  play(now) { this.tick(now); if (this.time >= this.duration) this.time = 0; this.playing = this.duration > 0; }
  pause(now) { this.tick(now); this.playing = false; }
  seek(time, now) { this.tick(now); this.time = Math.max(0, Math.min(this.duration, time)); }
  setRate(rate, now) { if (!Number.isFinite(rate) || rate <= 0) throw new RangeError('Playback rate must be positive'); this.tick(now); this.rate = rate; }
  reset(now) { this.pause(now); this.time = 0; }
}

const valid = Number.isFinite;
export function sampleAt(frames, time) {
  if (!frames.length) return { frame: null, index: -1, distance_m: null, gap: false };
  let lo = 0, hi = frames.length;
  while (lo < hi) { const mid = (lo + hi) >>> 1; if (frames[mid].t <= time) lo = mid + 1; else hi = mid; }
  const index = Math.max(0, lo - 1), frame = frames[index], next = frames[index + 1];
  const inGap = Boolean(next?.gap && time > frame.t && time < next.t);
  let distance_m = valid(frame.s_m) && valid(frame.speed_kmh) ? frame.s_m : null;
  if (next && time > frame.t) {
    if (inGap || !valid(next.s_m) || !valid(next.speed_kmh)) distance_m = null;
    else if (distance_m !== null && next.t > frame.t) {
      const dt = time - frame.t, span = next.t - frame.t;
      // Integral of linearly interpolated measured speed, consistent with Python trapezoids.
      distance_m += (frame.speed_kmh * dt + .5 * (next.speed_kmh - frame.speed_kmh) * dt * dt / span) / 3.6;
    }
  }
  return { frame, index, distance_m, gap: inGap };
}

export function previewAt(frames, time, horizon) {
  const current = sampleAt(frames, time);
  if (!current.frame || current.distance_m === null) return { distance_m: null, covered_s: 0, complete: false };
  const end = Math.min(time + horizon, frames.at(-1).t);
  let usableEnd = end;
  for (let i = current.index + 1; i < frames.length && frames[i].t <= end; i++) {
    if (frames[i].gap || !valid(frames[i].s_m) || !valid(frames[i].speed_kmh)) { usableEnd = Math.max(time, frames[i - 1].t); break; }
  }
  const target = sampleAt(frames, usableEnd);
  if (target.distance_m === null || (usableEnd === time && end > time)) return { distance_m: null, covered_s: 0, complete: false };
  return { distance_m: Math.max(0, target.distance_m - current.distance_m), covered_s: Math.max(0, usableEnd - time), complete: usableEnd - time >= horizon - 1e-6 };
}

export function formatTime(seconds) {
  const s = Math.max(0, Math.floor(seconds || 0));
  return `${Math.floor(s / 60).toString().padStart(2, '0')}:${(s % 60).toString().padStart(2, '0')}`;
}
