// Presentation only. Every number shown here is read from a replay frame that
// app/replay.py already computed by driving the existing Estimator over the
// original CSV timestamps. This file must never do engine physics, never
// interpolate a telemetry channel between two samples, and never invent a
// value for a channel the recording does not carry.
import { createScene, createEngineScene } from './scene.mjs';
import { PlaybackClock, sampleAt, previewAt, formatTime } from './playback.mjs';
import {
  EM_DASH, num, fmt, gearState, horizonRatio, previewCaption,
  thin, channelPath, cursorX, cursorY, CHART_W, CHART_H, PAD_X, PAD_Y,
  thresholdState, thresholdSpans, NEAR_K,
} from './panel.mjs';
import { t, DIR, LANGS, DEFAULT_LANG, resolveLang, applyTranslations } from './i18n.mjs';

const $ = id => document.getElementById(id);
const POLL_MS = 400;
const THEMES = ['light', 'dark'];
const STORE = { theme: 'grad.sim.theme', lang: 'grad.sim.lang' };

// localStorage throws in private mode and can come back empty after a clear,
// so every read and write is guarded and the page renders correctly without it.
function remember(key, value) {
  try { localStorage.setItem(key, value); } catch (e) { /* preference is a convenience */ }
}
function recall(key, allowed, fallback) {
  try {
    const v = localStorage.getItem(key);
    return allowed.includes(v) ? v : fallback;
  } catch (e) { return fallback; }
}

function setText(node, value) {
  if (node && node.textContent !== value) node.textContent = value;
}

function setClass(node, name, on) {
  if (node) node.classList.toggle(name, Boolean(on));
}

let currentLang = DEFAULT_LANG;

function showError(message, onRetry) {
  const box = $('error');
  if (!box) return;
  box.textContent = message || '';
  box.hidden = !message;
  // Re-picking the same <option> fires no change event, so without this the
  // only way out of a failed load is reloading the page.
  if (message && onRetry) {
    const again = document.createElement('button');
    again.type = 'button';
    again.textContent = t(currentLang, 'error.retry_button');
    again.style.cssText = 'margin-right:12px;border:1px solid currentColor;background:transparent;border-radius:6px;padding:3px 10px;font-size:11px;color:inherit';
    again.addEventListener('click', onRetry);
    box.appendChild(again);
  }
}

// ---------------------------------------------------------------- charts
// One static path per channel, drawn once per trip, plus a cursor that moves.
// Redrawing 30 000 points every frame is what makes a replay lab feel broken.
function renderChart(host, points, duration, specs, threshold) {
  if (!host) return null;
  const drawn = specs.map(s => ({ ...s, path: channelPath(points, s.key, duration) }))
    .filter(s => s.path);
  if (!drawn.length) {
    host.textContent = '';
    const note = document.createElement('p');
    note.className = 'chart-empty';
    note.textContent = t(currentLang, 'chart.unavailable');
    host.appendChild(note);
    return null;
  }
  const labels = drawn.map((s, i) => {
    const y = 11 + i * 11;
    return `<text class="axis-text" x="${CHART_W - PAD_X}" y="${y}" text-anchor="end">`
      + `${s.path.hi.toFixed(s.digits)} ${s.unit}</text>`;
  }).join('');
  // The threshold rule is drawn against the FIRST channel's scale, because
  // that is the channel it belongs to; it is omitted when the limit falls
  // outside the drawn range, rather than being clamped to an edge where it
  // would imply the drive came closer to it than it did.
  let rule = '';
  if (Number.isFinite(threshold) && drawn.length) {
    const p0 = drawn[0].path;
    if (threshold >= p0.lo && threshold <= p0.hi) {
      const y = cursorY(p0, threshold, false);
      rule = `<line class="limit-rule" x1="${PAD_X}" y1="${y.toFixed(1)}" x2="${CHART_W - PAD_X}" y2="${y.toFixed(1)}"/>`;
    }
  }
  host.innerHTML = `<svg viewBox="0 0 ${CHART_W} ${CHART_H}" preserveAspectRatio="none" role="presentation">`
    + `<line class="grid" x1="${PAD_X}" y1="${CHART_H - PAD_Y}" x2="${CHART_W - PAD_X}" y2="${CHART_H - PAD_Y}"/>`
    + rule
    + drawn.map(s => `<path d="${s.path.d}" fill="none" stroke="${s.stroke}" stroke-width="1.5" stroke-linejoin="round" stroke-linecap="round"/>`).join('')
    + labels
    + `<line class="cursor" x1="0" y1="0" x2="0" y2="${CHART_H}"/>`
    + drawn.map(() => '<circle class="cursor-dot" r="2.6" cx="-10" cy="-10"/>').join('')
    + '</svg>';
  return {
    cursor: host.querySelector('.cursor'),
    dots: [...host.querySelectorAll('.cursor-dot')],
    specs: drawn,
  };
}

function moveCursor(chart, frame, time, duration) {
  if (!chart) return;
  const x = cursorX(time, duration);
  chart.cursor.setAttribute('x1', x);
  chart.cursor.setAttribute('x2', x);
  chart.specs.forEach((s, i) => {
    const dot = chart.dots[i];
    const y = cursorY(s.path, frame ? frame[s.key] : null, frame && frame.gap);
    if (y === null) { dot.setAttribute('cx', -10); return; }
    dot.setAttribute('cx', x);
    dot.setAttribute('cy', y);
  });
}

// ---------------------------------------------------------------- gears
// Driven by the ratio count the server read off Vehicle, never by a literal 8.
// If the gearbox is ever corrected again the strip follows it; a hardcoded 8
// would have kept showing eight cells for a seven-speed and nobody would know.
function buildGearStrip(host, count) {
  if (!host) return [];
  host.innerHTML = '';
  host.style.gridTemplateColumns = `repeat(${count}, 1fr)`;
  return Array.from({ length: count }, (_, i) => {
    const cell = document.createElement('div');
    cell.className = 'gear';
    cell.setAttribute('role', 'listitem');
    cell.textContent = String(i + 1);
    host.appendChild(cell);
    return cell;
  });
}

function paintGears(cells, frame, lang) {
  const state = gearState(frame, lang);
  cells.forEach((cell, i) => {
    const on = state.gear === i + 1;
    setClass(cell, 'current', on);
    setClass(cell, 'estimated', on && state.estimated);
    if (on) cell.setAttribute('aria-current', 'true');
    else cell.removeAttribute('aria-current');
  });
  const label = $('gear-source');
  setText(label, state.sourceText);
  if (label) label.className = `source-label${state.source === 'unavailable' ? '' : ` ${state.source}`}`;
  setText($('gear-note'), state.note);
}

function markShifts(host, events, duration) {
  if (!host) return;
  host.innerHTML = '';
  if (!(duration > 0)) return;
  for (const e of events) {
    const tick = document.createElement('i');
    tick.style.left = `${Math.min(100, Math.max(0, (e.t / duration) * 100))}%`;
    if (e.source === 'estimated') tick.className = 'estimated';
    tick.title = `${formatTime(e.t)} · ${e.from_gear} → ${e.to_gear}`;
    host.appendChild(tick);
  }
}

// ---------------------------------------------------------------- boot
async function getJSON(url) {
  const res = await fetch(url, { headers: { Accept: 'application/json' } });
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
  return res.json();
}

const wait = ms => new Promise(resolve => setTimeout(resolve, ms));

function mountScene(host, factory, label) {
  try {
    return factory(host);
  } catch (err) {
    if (host) {
      host.textContent = '';
      const note = document.createElement('p');
      note.className = 'webgl-error';
      note.textContent = t(currentLang, 'scene.webgl_error', { label });
      host.appendChild(note);
    }
    console.error(err);
    return null;
  }
}

async function start() {
  const world = mountScene($('world'), createScene, t(currentLang, 'scene.label.world'));
  const engine = mountScene($('engine'), createEngineScene, t(currentLang, 'scene.label.engine'));
  let gearCells = [];
  const clock = new PlaybackClock(0);

  let frames = [];
  let events = [];
  let meta = null;
  let driveChart = null;
  let thermalChart = null;
  let horizon = 30;
  let limits = {};
  let turbLimitC = null;
  let lastFrame;          // undefined until a frame has actually been painted
  let wasPlaying = false;
  let drawnTime = -1;
  let loadToken = 0;

  const select = $('trip');
  const seek = $('seek');
  const play = $('play');
  const restart = $('restart');
  const rate = $('rate');
  const horizonSelect = $('horizon');

  // ------------------------------------------------------------ catalog
  let catalog;
  try {
    catalog = await getJSON('/api/replay/trips');
  } catch (err) {
    showError(t(currentLang, 'error.catalog', { message: err.message }));
    setText($('load-title'), t(currentLang, 'load.title_failed'));
    setText($('load-detail'), t(currentLang, 'load.detail_no_server'));
    return;
  }

  const horizons = (catalog.preview_s || [30]).slice().sort((a, b) => a - b);
  horizon = horizons.includes(30) ? 30 : horizons[horizons.length - 1];
  if (horizonSelect) {
    horizonSelect.innerHTML = horizons
      .map(h => `<option value="${h}"${h === horizon ? ' selected' : ''}>H = ${h} s</option>`).join('');
  }

  limits = catalog.limits || {};
  turbLimitC = num(limits.turb_c);
  setText($('limit-caption'), turbLimitC === null ? ''
    : t(currentLang, 'limit.caption', { value: turbLimitC.toFixed(1) }));
  const vehicle = catalog.vehicle || {};
  gearCells = buildGearStrip($('gears'), (vehicle.gears || []).length || 8);
  // Read from Vehicle like the ratios are, so a gearbox correction cannot
  // leave the label naming a transmission the model no longer runs.
  if (vehicle.name) setText($('gearbox-name'), vehicle.name);
  setText($('gear-method'), vehicle.gears
    ? t(currentLang, 'method.gear_ratios', {
      name: vehicle.name, ratios: vehicle.gears.join(' \u00b7 '),
      final_drive: vehicle.final_drive,
      tolerance: (vehicle.inference_tolerance * 100).toFixed(0),
      min_kmh: vehicle.inference_min_kmh,
    })
    : '');

  const trips = (catalog.trips || []).filter(t => t.rows > 0);
  if (!trips.length) { showError(t(currentLang, 'error.no_recordings')); return; }
  trips.sort((a, b) => b.duration_s - a.duration_s);
  function fillTripOptions() {
    const keep = select.value;
    select.textContent = '';
    for (const trip of trips) {
      const option = document.createElement('option');
      option.value = trip.id;
      option.textContent = t(currentLang, 'trip.option',
        { id: trip.id.split('-')[0], minutes: (trip.duration_s / 60).toFixed(1) });
      select.appendChild(option);
    }
    if (keep) select.value = keep;
  }
  fillTripOptions();

  // Measured 21 Sep on this machine: 79 rows/s over 3f64372e's 276 rows and
  // 74 rows/s over 670063b2's 2923. The build is the physics running once per
  // sample; it is not a spinner that can be hurried. Re-measure on a new box.
  const buildSeconds = trip => Math.round(trip.rows / 75);

  function describeTrip(trip) {
    const bits = [t(currentLang, 'trip.samples', { count: trip.rows })];
    const secs = buildSeconds(trip);
    bits.push(secs >= 90 ? t(currentLang, 'trip.build_minutes', { minutes: Math.round(secs / 60) })
      : t(currentLang, 'trip.build_seconds', { seconds: secs }));
    bits.push(t(currentLang, trip.has_gear ? 'trip.gear_channel' : 'trip.no_gear_channel'));
    if (!trip.has_speed) bits.push(t(currentLang, 'trip.no_speed_channel'));
    else if (!trip.has_motion) bits.push(t(currentLang, 'trip.no_motion'));
    if (!trip.has_oil) bits.push(t(currentLang, 'trip.oil_estimated'));
    setText($('trip-meta'), bits.join(t(currentLang, 'trip.meta_separator')));
  }

  // ------------------------------------------------------------ loading
  function setLoading(visible, title, detail, progress) {
    const card = $('loading');
    if (card) card.hidden = !visible;
    if (title !== undefined) setText($('load-title'), title);
    if (detail !== undefined) setText($('load-detail'), detail);
    const bar = $('load-progress');
    if (bar && progress !== undefined) bar.value = Math.max(0, Math.min(1, progress));
  }

  function setControlsEnabled(on) {
    [play, restart, seek].forEach(el => { if (el) el.disabled = !on; });
  }

  async function loadTrip(tripId) {
    const token = ++loadToken;
    setControlsEnabled(false);
    clock.reset(performance.now());
    frames = []; events = []; meta = null;
    driveChart = null; thermalChart = null;
    showError('');
    // `undefined`, not null: draw() compares `frame !== lastFrame` and
    // sampleAt returns null on an empty set, so leaving null here made the
    // comparison false and the PREVIOUS trip's readings stayed on screen,
    // under the new trip's name, for the whole build.
    lastFrame = undefined;
    drawnTime = -1;
    draw(0, true);
    const chosen = trips.find(t => t.id === tripId);
    const budget = chosen ? buildSeconds(chosen) : 0;
    setLoading(true, t(currentLang, 'load.title'),
      budget >= 90 ? t(currentLang, 'load.detail_budget_minutes', { minutes: Math.round(budget / 60) })
        : t(currentLang, 'load.detail_budget_seconds', { seconds: budget }), 0);
    // Only this first request may cancel a build already running: it is the
    // one that carries a person's decision. Every poll after it waits.
    let preempt = true;
    for (;;) {
      let payload;
      try {
        const q = preempt ? '?preempt=1' : '';
        payload = await getJSON(`/api/replay/trips/${encodeURIComponent(tripId)}${q}`);
        preempt = false;
      } catch (err) {
        if (token !== loadToken) return;
        setLoading(true, t(currentLang, 'load.title_failed_compute'),
          t(currentLang, 'load.detail_server_error', { message: err.message }), 0);
        showError(t(currentLang, 'error.trip_prepare', { message: err.message }), () => loadTrip(tripId));
        return;
      }
      if (token !== loadToken) return;
      if (payload.status === 'ready') { applyTrip(payload); return; }
      if (payload.status === 'error') {
        setLoading(true, t(currentLang, 'load.title_failed_compute'),
          payload.message || t(currentLang, 'error.unknown_reason'), 0);
        showError(t(currentLang, 'error.trip_prepare',
          { message: payload.message || t(currentLang, 'error.unknown_reason_inline') }),
        () => loadTrip(tripId));
        return;
      }
      const busy = payload.status === 'busy';
      setLoading(true, t(currentLang, busy ? 'load.title_busy' : 'load.title'),
        busy ? t(currentLang, 'load.detail_busy')
          : t(currentLang, 'load.detail_progress',
            { percent: Math.round((payload.progress || 0) * 100) }),
        busy ? 0 : payload.progress || 0);
      await wait(POLL_MS);
    }
  }

  function applyTrip(payload) {
    frames = payload.frames || [];
    events = payload.events || [];
    meta = payload.meta || null;
    const duration = meta?.duration_s || frames[frames.length - 1]?.t || 0;
    clock.duration = duration;
    clock.reset(performance.now());
    if (seek) { seek.max = String(duration || 1); seek.step = '0.05'; seek.value = '0'; }
    setText($('duration'), formatTime(duration));
    markShifts($('shift-markers'), events, duration);

    const points = thin(frames);
    driveChart = renderChart($('drive-chart'), points, duration, [
      { key: 'speed_kmh', stroke: '#779b85', unit: 'km/h', digits: 0 },
      { key: 'rpm', stroke: '#b9b078', unit: 'rpm', digits: 0 },
    ]);
    thermalChart = renderChart($('thermal-chart'), points, duration, [
      { key: 'turbine_c', stroke: '#c09463', unit: '°C', digits: 0 },
      { key: 'oil_c', stroke: '#8ca1a0', unit: '°C', digits: 0 },
    ], turbLimitC);
    paintThresholdBands(frames, duration);

    setText($('fingerprint'), meta ? JSON.stringify(meta, null, 2) : t(currentLang, 'fingerprint.none'));
    setControlsEnabled(true);
    setLoading(false);
    draw(0, true);
  }

  // Spans of the timeline where the ESTIMATE sat at or above the threshold.
  // This is the same quantity as "seconds above the trigger" in the project
  // notes, measured here per drive rather than asserted.
  function paintThresholdBands(all, duration) {
    const host = $('limit-bands');
    const summary = $('limit-summary');
    if (host) host.textContent = '';
    if (!(duration > 0) || turbLimitC === null) { setText(summary, ''); return; }
    const { spans, total_s } = thresholdSpans(all, turbLimitC);
    if (host) {
      for (const span of spans) {
        const band = document.createElement('i');
        const left = (span.from / duration) * 100;
        const width = Math.max(0.4, ((span.to - span.from) / duration) * 100);
        band.style.insetInlineStart = `${left}%`;
        band.style.width = `${width}%`;
        host.appendChild(band);
      }
    }
    setText(summary, spans.length
      ? t(currentLang, 'limit.time_above', {
        seconds: total_s.toFixed(0), total: duration.toFixed(0),
        percent: ((total_s / duration) * 100).toFixed(3),
      })
      : t(currentLang, 'limit.never'));
  }

  // ------------------------------------------------------------ per frame
  function draw(time, force = false) {
    const duration = clock.duration;
    const picked = sampleAt(frames, time);
    const frame = picked.frame;
    const changed = force || frame !== lastFrame;
    lastFrame = frame;

    const preview = previewAt(frames, time, horizon);
    world?.update(frame, { distance_m: picked.distance_m, preview_m: preview.distance_m });

    setText($('current-time'), formatTime(time));
    if (seek && document.activeElement !== seek) seek.value = String(time);
    setText($('sample-time'), `t = ${time.toFixed(1)} s`);
    moveCursor(driveChart, frame, time, duration);
    moveCursor(thermalChart, frame, time, duration);

    // H / tau. tau is the Estimator's own flow-dependent value, not a constant.
    const ratio = horizonRatio(horizon, frame ? frame.tau_turb_s : null);
    setText($('h-value'), String(horizon));
    setText($('h-distance'), preview.distance_m === null ? EM_DASH : Math.round(preview.distance_m).toString());
    setText($('tau-value'), ratio.tauText);
    setText($('h-tau'), ratio.ratioText);
    setText($('h-coverage'), previewCaption(preview, currentLang));

    if (!changed) return;

    engine?.update(frame);
    paintGears(gearCells, frame, currentLang);

    setText($('speed'), fmt(frame?.speed_kmh, 0));
    setText($('rpm'), fmt(frame?.rpm, 0));
    const bar = $('rpm-bar');
    if (bar) bar.style.transform = `scaleX(${Math.min(1, (num(frame?.rpm) || 0) / 7000)})`;

    setText($('turbine'), fmt(frame?.turbine_c, 0));
    // Threshold highlight. Both facts travel with it: the limit is one this
    // project chose, and the value compared against it is a model output.
    const limitState = thresholdState(frame?.turbine_c, turbLimitC, frame?.turbine_ss_c);
    const turbineValue = $('turbine');
    setClass(turbineValue, 'at-limit', limitState.level === 'over');
    setClass(turbineValue, 'near-limit', limitState.level === 'near');
    document.body?.classList.toggle('limit-over', limitState.level === 'over');
    document.body?.classList.toggle('limit-near', limitState.level === 'near');
    const badge = $('limit-badge');
    if (badge) {
      badge.hidden = limitState.level !== 'over' && limitState.level !== 'near';
      badge.className = `limit-badge ${limitState.level}`;
      if (!badge.hidden) {
        setText(badge, limitState.level === 'over'
          ? t(currentLang, 'limit.badge_over') : t(currentLang, 'limit.badge_near'));
        badge.title = limitState.level === 'over'
          ? t(currentLang, 'limit.over_note', { over: limitState.over.toFixed(0) })
          : (limitState.heading
            ? t(currentLang, 'limit.heading_note', { steady: num(frame?.turbine_ss_c).toFixed(0) })
            : t(currentLang, 'limit.near_note', { margin: limitState.margin.toFixed(0) }));
      }
    }
    setText($('coolant'), fmt(frame?.coolant_c, 0));
    setText($('oil'), fmt(frame?.oil_c, 0));
    const oilDot = $('oil-dot');
    if (oilDot) oilDot.className = `source-dot ${frame?.oil_source || 'unavailable'}`;
    // Coolant is measured when the recording carries it and absent otherwise;
    // a hardcoded "recorded" dot would claim a sensor on a log without one.
    const coolantDot = $('coolant-dot');
    if (coolantDot) coolantDot.className = `source-dot ${num(frame?.coolant_c) === null ? 'unavailable' : 'recorded'}`;

    setText($('fuel'), fmt(frame?.fuel_gps, 2));
    setText($('torque'), fmt(frame?.torque_nm, 0));
    setText($('map'), fmt(frame?.map_kpa, 0));
    // grade_pct is None on every frame of every recording: no grade channel,
    // no GPS, no altitude. The scene's slope is decoration and says so.
    setText($('grade'), num(frame?.grade_pct) === null ? t(currentLang, 'value.unavailable') : fmt(frame.grade_pct, 1));
    // distance_partial means a gap or a missing speed already broke the
    // integral, so the odometer is a LOWER BOUND, not the distance driven.
    const partial = Boolean(frame?.distance_partial);
    setText($('distance'), picked.distance_m === null ? EM_DASH
      : `${partial ? '≥ ' : ''}${(picked.distance_m / 1000).toFixed(2)}`);
    setClass($('distance'), 'odo-partial', partial);
    const distDot = $('distance-dot');
    if (distDot) distDot.className = `source-dot ${picked.distance_m === null ? 'unavailable' : (partial ? 'estimated' : 'recorded')}`;

    // The car laps a short loop on a long drive. Saying which lap it is on
    // stops the repeated decorative hill from reading as the recorded road.
    const lap = world?.loopLength_m;
    setText($('lap-note'), lap && picked.distance_m !== null
      ? t(currentLang, 'road.lap_note',
        { lap: Math.floor(picked.distance_m / lap) + 1, km: (lap / 1000).toFixed(1) })
      : '');

    const status = $('sample-status');
    if (picked.gap) setText(status, t(currentLang, 'sample.gap'));
    else if (frame) setText(status, t(currentLang, 'sample.index',
      { index: picked.index + 1, total: frames.length }));
    else setText(status, t(currentLang, 'sample.waiting'));
    setClass(status, 'gap-message', picked.gap);

    const seedNote = $('seed-note');
    const band = frame ? num(frame.seed_band_k) : null;
    if (frame?.warming_up && band !== null) {
      setText(seedNote, t(currentLang, 'seed.warming', { band: band.toFixed(0) }));
      setClass(seedNote, 'warming', true);
    } else {
      setText(seedNote, t(currentLang, 'seed.model_output'));
      setClass(seedNote, 'warming', false);
    }
  }

  // ------------------------------------------------------------ controls
  function syncPlayButton() {
    const icon = play?.querySelector('use');
    const text = play?.querySelector('span');
    if (icon) icon.setAttribute('href', clock.playing ? '#i-pause' : '#i-play');
    if (text) text.textContent = t(currentLang, clock.playing ? 'transport.pause' : 'transport.play');
    play?.setAttribute('aria-label',
      t(currentLang, clock.playing ? 'transport.pause_aria' : 'transport.play_aria'));
  }

  play?.addEventListener('click', () => {
    const now = performance.now();
    if (clock.playing) clock.pause(now); else clock.play(now);
    syncPlayButton();
  });
  restart?.addEventListener('click', () => {
    clock.reset(performance.now());
    syncPlayButton();
    draw(0, true);
  });
  seek?.addEventListener('input', () => {
    clock.seek(Number(seek.value), performance.now());
    draw(clock.time, true);
  });
  // Presentation rate only: the same trip time always selects the same sample.
  rate?.addEventListener('change', () => clock.setRate(Number(rate.value), performance.now()));
  horizonSelect?.addEventListener('change', () => {
    horizon = Number(horizonSelect.value);
    draw(clock.time, true);
  });
  $('follow')?.addEventListener('click', () => {
    const btn = $('follow');
    const on = btn.getAttribute('aria-pressed') !== 'true';
    btn.setAttribute('aria-pressed', String(on));
    world?.setFollow(on);
  });
  $('zoom-in')?.addEventListener('click', () => world?.zoom(1.25));
  $('zoom-out')?.addEventListener('click', () => world?.zoom(0.8));
  $('camera-reset')?.addEventListener('click', () => {
    world?.resetCamera();
    $('follow')?.setAttribute('aria-pressed', 'false');
  });
  $('details-toggle')?.addEventListener('click', () => {
    const panel = $('method-details');
    const open = panel.hidden;
    panel.hidden = !open;
    $('details-toggle').setAttribute('aria-expanded', String(open));
  });
  select?.addEventListener('change', () => {
    const trip = trips.find(t => t.id === select.value);
    if (trip) describeTrip(trip);
    syncPlayButton();
    loadTrip(select.value);
  });

  // ------------------------------------------------------- theme + language
  // Both are presentation only. Neither touches a frame, a limit or a number:
  // switching to English or to dark must never change a value on this page.
  function applyTheme(name) {
    const theme = THEMES.includes(name) ? name : 'light';
    document.documentElement.dataset.theme = theme;
    world?.setTheme?.(theme);
    engine?.setTheme?.(theme);
    const meta = document.querySelector('meta[name="theme-color"]');
    if (meta) {
      meta.setAttribute('content',
        getComputedStyle(document.documentElement).getPropertyValue('--bg').trim() || '#f4f3ed');
    }
    const button = $('theme-toggle');
    if (button) {
      const next = theme === 'dark' ? 'light' : 'dark';
      button.title = t(currentLang, next === 'dark' ? 'theme.to_dark' : 'theme.to_light');
      button.setAttribute('aria-pressed', String(theme === 'dark'));
      const icon = button.querySelector('use');
      if (icon) icon.setAttribute('href', theme === 'dark' ? '#i-sun' : '#i-moon');
    }
    remember(STORE.theme, theme);
  }

  function applyLanguage(name) {
    currentLang = resolveLang(name);
    applyTranslations(document, currentLang);
    const button = $('lang-toggle');
    if (button) {
      const other = currentLang === 'ar' ? 'en' : 'ar';
      button.title = t(currentLang, other === 'en' ? 'lang.switch_to_english' : 'lang.switch_to_arabic');
      const label = button.querySelector('span');
      if (label) label.textContent = other === 'en' ? 'EN' : 'AR';
    }
    // Everything the dictionary cannot reach because JS wrote it: re-render it
    // from the data we already hold rather than refetching or recomputing.
    if (horizonSelect) {
      horizonSelect.innerHTML = horizons.map(h =>
        `<option value="${h}"${h === horizon ? ' selected' : ''}>`
        + `${t(currentLang, 'preview.horizon_option', { seconds: h })}</option>`).join('');
    }
    if (typeof fillTripOptions === 'function') fillTripOptions();
    const chosen = trips.find(x => x.id === select.value);
    if (chosen) describeTrip(chosen);
    setText($('gear-method'), vehicle.gears
      ? t(currentLang, 'method.gear_ratios', {
        name: vehicle.name, ratios: vehicle.gears.join(' \u00b7 '),
        final_drive: vehicle.final_drive,
        tolerance: (vehicle.inference_tolerance * 100).toFixed(0),
        min_kmh: vehicle.inference_min_kmh,
      })
      : '');
    setText($('limit-caption'), turbLimitC === null ? ''
      : t(currentLang, 'limit.caption', { value: turbLimitC.toFixed(1) }));
    markShifts($('shift-markers'), events, clock.duration);
    paintThresholdBands(frames, clock.duration);
    syncPlayButton();
    draw(clock.time, true);
    remember(STORE.lang, currentLang);
  }

  $('theme-toggle')?.addEventListener('click', () => {
    applyTheme(document.documentElement.dataset.theme === 'dark' ? 'light' : 'dark');
  });
  $('lang-toggle')?.addEventListener('click', () => {
    applyLanguage(currentLang === 'ar' ? 'en' : 'ar');
  });

  applyTheme(recall(STORE.theme, THEMES,
    window.matchMedia?.('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'));
  applyLanguage(recall(STORE.lang, LANGS, DEFAULT_LANG));

  world?.setFollow($('follow')?.getAttribute('aria-pressed') === 'true');

  function loop(now) {
    const time = clock.tick(now);
    // Idle frames cost a WebGL draw for nothing; OrbitControls re-renders itself.
    if (time !== drawnTime) { draw(time); drawnTime = time; }
    if (clock.playing !== wasPlaying) { wasPlaying = clock.playing; syncPlayButton(); }
    requestAnimationFrame(loop);
  }
  requestAnimationFrame(loop);

  // Open on the QUICKEST recording that actually moves, not the longest.
  // The list is sorted longest-first because that is the useful order to read,
  // but auto-loading trips[0] meant opening the page started a multi-minute
  // build of the two-hour drive before anything could be seen.
  const movers = trips.filter(t => t.has_motion);
  const first = (movers.length ? movers : trips).reduce((a, b) => (a.rows <= b.rows ? a : b));
  select.value = first.id;
  describeTrip(first);
  await loadTrip(first.id);
}

start().catch(err => {
  console.error(err);
  showError(t(currentLang, 'error.unexpected', { message: err.message }));
});
