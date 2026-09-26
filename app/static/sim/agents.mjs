// The agent replay page (/agents): wiring, polling, the clock, the verdict box,
// the badge, the timeline and the whole-route profile.
//
// PRESENTATION ONLY. Every number drawn here arrives in a frame or a road that
// app/agent_trace.py computed on the server, and app/test_agents.py proves
// those frames are evaluate.run_episode's own episode (==, no tolerance). This
// file never does engine physics, never computes a statistic and never
// computes a difference between the two cars: the page shows no winner.
//
// Lane 0 is always the sighted agent and lane 1 the blind one, in run_lanes
// order and in meta.agents order.
//
// M1: the picker is READ-ONLY. It shows ?runs=&seed=&ep= from the address and
// nothing computes until «احسب» is pressed. Nothing is stored in the browser
// except the lab's own theme and language preferences.
import './agents-strings.mjs';
import { t, LANGS, DEFAULT_LANG, resolveLang, applyTranslations } from './i18n.mjs';
import { PlaybackClock, formatTime } from './playback.mjs';
import {
  DT, PROFILE_VE, parseEpisodeQuery, appendFrames, createPlayState, playOrWait,
  pauseByUser, resumeIfStalled, settleDone, episodeAt, profilePoints, previewMarks, gradeRamp,
} from './agent-view.mjs';

const $ = id => document.getElementById(id);
const POLL_MS = 400;
const THEMES = ['light', 'dark'];
const STORE = { theme: 'grad.sim.theme', lang: 'grad.sim.lang' };
const EM_DASH = '—';
const LANES = ['sighted', 'blind'];
const LANE_LABEL = ['agents.car.sighted', 'agents.car.blind'];
const PROFILE_W = 1000;
const PROFILE_PAD = 24;
const KM_STEP = 5;   // the profile's horizontal scale: a label every 5 km

let currentLang = DEFAULT_LANG;

const state = {
  query: parseEpisodeQuery(window.location.search),
  frames: [],
  road: null,
  meta: null,
  metaKey: null,
  done: false,
  loadToken: 0,
  polling: null,
  play: createPlayState(new PlaybackClock(0)),
  device: null,
  versions: null,
  load: null,      // { text: () => string, progress } for the loading card
  error: null,     // { text: () => string, items, retry } for #error
  profile: null,   // { sx, ve, height, car, ticks } once the road is drawn
  lastK: -2,
  drawnTime: -1,
  wasPlaying: false,
};

// ---------------------------------------------------------------- helpers
function remember(key, value) {
  try { localStorage.setItem(key, value); } catch (e) { /* a preference is a convenience */ }
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
function el(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}
const num = v => (typeof v === 'number' && Number.isFinite(v) ? v : null);
function fmt(v, digits) {
  const n = num(v);
  return n === null ? EM_DASH : n.toFixed(digits);
}
// Thousands are grouped with U+202F, a narrow no-break space of bidi class CS.
// A plain space is class WS: in the Arabic page each digit group then becomes
// its own run and the line swaps them, so 300 000 is drawn "000 300" (UAX #9
// W4 joins two numbers only across a single CS). agents-page-run.test.mjs.
function fmtInt(v) {
  const n = num(v);
  return n === null ? EM_DASH : String(Math.round(n)).replace(/\B(?=(\d{3})+(?!\d))/g, '\u202f');
}
const wait = ms => new Promise(resolve => setTimeout(resolve, ms));
const keyOf = q => `${q.runs}/${q.seed}/${q.ep}`;

// fingerprint.format_budget writes "trained N steps of M requested, ..."; the
// page shows N and falls back to the whole line rather than guess.
function budgetSteps(line) {
  const m = /^trained (\d+) steps/.exec(line || '');
  return m ? fmtInt(Number(m[1])) : (line || EM_DASH);
}

// ---------------------------------------------------------------- status
// Both hold a function, not a string, so a language switch re-renders them.
function showLoad(text, progress = 0) {
  state.load = text ? { text, progress } : null;
  renderLoad();
}
function renderLoad() {
  const card = $('loading');
  if (!card) return;
  card.hidden = !state.load;
  if (!state.load) return;
  setText($('load-title'), state.load.text());
  setText($('load-detail'), state.query ? keyOf(state.query) : '');
  const bar = $('load-progress');
  if (bar) bar.value = Math.max(0, Math.min(1, state.load.progress || 0));
}
function showError(text, { retry = null, items = [] } = {}) {
  state.error = text ? { text, retry, items } : null;
  renderError();
}
function renderError() {
  const box = $('error');
  if (!box) return;
  box.textContent = '';
  box.hidden = !state.error;
  if (!state.error) return;
  box.appendChild(el('span', '', state.error.text()));
  if (state.error.items.length) {
    const list = el('ul');
    for (const item of state.error.items) {
      const li = el('li', '', String(item));
      li.dir = 'ltr';
      list.appendChild(li);
    }
    box.appendChild(list);
  }
  const retry = state.error.retry;
  if (retry) {
    const again = el('button', 'retry-button', t(currentLang, 'agents.load.retry'));
    again.type = 'button';
    again.addEventListener('click', () => { again.disabled = true; retry(); }, { once: true });
    box.appendChild(again);
  }
}

// ---------------------------------------------------------------- compute
function setControlsEnabled(on) {
  for (const id of ['play', 'restart', 'seek']) {
    const node = $(id);
    if (node) node.disabled = !on;
  }
}

function episodeUrl(since, preempt) {
  const q = state.query;
  const params = new URLSearchParams({
    runs: q.runs, seed: String(q.seed), ep: String(q.ep), since: String(since),
  });
  if (preempt) params.set('preempt', '1');
  return `/api/agents/episode?${params}`;
}

// «احسب». The one request that carries a person's decision sends preempt=1;
// every poll after it waits its turn (app.replay's rule, kept here).
function compute() {
  if (!state.query) return;
  state.loadToken += 1;
  const token = state.loadToken;
  const now = performance.now();
  pauseByUser(state.play, now);
  state.play = createPlayState(new PlaybackClock(0));
  state.play.clock.setRate(Number($('rate')?.value) || 1, now);
  if (state.metaKey !== keyOf(state.query)) { state.meta = null; state.road = null; }
  state.frames = [];
  state.done = false;
  state.device = null;
  state.versions = null;
  state.lastK = -2;
  showError(null);
  const prompt = $('scene-prompt');
  if (prompt) prompt.hidden = true;
  setControlsEnabled(false);
  showLoad(() => t(currentLang, 'agents.load.networks'), 0);
  renderAll();
  poll(token, true);
}

async function poll(token, preempt) {
  if (state.polling === token) return;
  state.polling = token;
  try {
    for (;;) {
      let res;
      let body = null;
      try {
        res = await fetch(episodeUrl(state.frames.length, preempt),
          { headers: { Accept: 'application/json' }, cache: 'no-store' });
        body = await res.json().catch(() => null);
      } catch (err) {
        if (token !== state.loadToken) return;
        // Frames already received stay playable; the retry resumes from them.
        showLoad(null);
        showError(() => t(currentLang, 'agents.load.server_down'), { retry: () => poll(token, false) });
        return;
      }
      if (token !== state.loadToken) return;   // a newer «احسب» owns the page
      preempt = false;
      if (!handle(res.status, body)) return;
      await wait(POLL_MS);
      if (token !== state.loadToken) return;
    }
  } finally {
    if (state.polling === token) state.polling = null;
  }
}

function stop(text, options) {
  showLoad(null);
  showError(text, options);
  renderTimeline();
}

// One response. Returns true to keep polling.
function handle(status, body) {
  if (status === 404) { stop(() => t(currentLang, 'agents.load.not_found')); return false; }
  if (status === 409) {
    stop(() => t(currentLang, 'agents.load.refused'), { items: (body && body.problems) || [] });
    return false;
  }
  if (status === 503) { stop(() => t(currentLang, 'agents.load.no_sb3')); return false; }
  if (status !== 200 || !body) {
    const message = `HTTP ${status}`;
    stop(() => t(currentLang, 'agents.load.error', { message }), { retry: compute });
    return false;
  }
  // The server answered, so an earlier "server unavailable" (and its retry
  // button) is no longer true; a retry resumes polling without «احسب».
  if (state.error) showError(null);
  if (body.meta && body.road) applyMeta(body.meta, body.road);
  if (body.device) state.device = body.device;
  if (body.versions) state.versions = body.versions;
  // Only a slice that starts exactly where the held frames end is kept; a
  // stale or overlapping response changes nothing (agent-view.appendFrames).
  const accepted = appendFrames(state.frames, body);
  const now = performance.now();
  if (accepted && body.frames.length) {
    resumeIfStalled(state.play, state.frames.length * DT, now);
    setControlsEnabled(true);
    // Paused at 0:00 the clock never moves, so the animation loop never redraws:
    // draw once when frame 0 first exists, or the panel reads — until play.
    if (state.lastK < 0) draw(state.play.clock.time, true);
  }
  const steps = num(body.steps) || 1;
  if (body.status === 'loading') showLoad(() => t(currentLang, 'agents.load.networks'), 0);
  else if (body.status === 'busy') {
    const a = body.active || {};
    showLoad(() => t(currentLang, 'agents.load.busy', { runs: a.runs, seed: a.seed, ep: a.ep }), 0);
  } else if (body.status === 'building') {
    const percent = Math.round(state.frames.length / steps * 100);
    showLoad(() => t(currentLang, 'agents.load.building', { percent }), state.frames.length / steps);
  } else if (body.status === 'ready' && accepted) {
    state.done = true;
    settleDone(state.play, state.frames.length * DT, now);
    showLoad(null);
    renderAll();
    return false;
  } else if (body.status === 'error') {
    const message = body.message || '';
    stop(() => t(currentLang, 'agents.load.error', { message }), { retry: compute });
    return false;
  }
  renderTimeline();
  return true;
}

// ---------------------------------------------------------------- meta
function applyMeta(meta, road) {
  const key = keyOf({ runs: meta.runs, seed: meta.seed, ep: meta.ep });
  if (state.metaKey === key && state.road) return;
  state.metaKey = key;
  state.meta = meta;
  state.road = road;
  const more = $('verdict-more');
  if (more) more.open = !window.matchMedia?.('(max-width: 760px)').matches;
  drawProfile(road);
  renderAll();
}

function option(select, text) {
  if (!select) return;
  select.textContent = '';
  const o = el('option', '', text);
  o.selected = true;
  select.appendChild(o);
}

function renderPicker() {
  const q = state.query;
  const m = state.meta;
  const button = $('compute');
  if (button) button.disabled = !q;
  const note = $('pick-note');
  if (note) note.textContent = '';
  if (!q) {
    for (const id of ['pick-experiment', 'pick-pair', 'pick-episode']) option($(id), EM_DASH);
    setText(note, t(currentLang, 'agents.pick.none'));
    return;
  }
  const short = m?.verdict?.short?.[currentLang];
  option($('pick-experiment'), m ? (short ? `${m.experiment} · ${short}` : m.experiment) : q.runs);
  option($('pick-pair'), t(currentLang, 'agents.pick.pair_option', { seed: q.seed }));
  const e = m?.episode;
  const episodeText = e
    ? t(currentLang, 'agents.pick.episode_option', {
      idx: m.ep,
      start: fmt(e.climb_start_s, 0),
      grade: num(e.grade) === null ? EM_DASH : fmt(e.grade * 100, 1),
      w0: fmt(e.weights[0], 2),
      w1: fmt(e.weights[1], 2),
      w2: fmt(e.weights[2], 2),
    })
    : `${t(currentLang, 'agents.pick.episode')} ${q.ep}`;
  option($('pick-episode'), episodeText);
  if (!note || !m) return;
  // The select may truncate on a narrow screen; the weights must stay legible.
  note.appendChild(el('span', '', episodeText));
  (m.agents || []).forEach((agent, i) => {
    const line = el('span', LANES[i]);
    line.appendChild(el('i', 'lane-dot'));
    line.appendChild(el('span', '', `${t(currentLang, LANE_LABEL[i])} · ${t(currentLang, 'agents.pick.budget', { budget: budgetSteps(agent.budget_line) })}`));
    note.appendChild(line);
  });
}

function renderBadge() {
  const m = state.meta;
  if (!m) { setText($('sim-badge'), t(currentLang, 'agents.badge.short')); return; }
  // Figures from meta only: the episode's own grade, the scenario's speed and
  // ambient. Nothing here is read from a document or a recorded drive.
  setText($('sim-badge'), t(currentLang, 'agents.badge', {
    grade: num(m.episode?.grade) === null ? EM_DASH : fmt(m.episode.grade * 100, 1),
    v: fmt(m.scenario?.v_kmh, 0),
    t: fmt(m.scenario?.t_amb_c, 0),
  }));
}

// The verdict is QUOTED, never computed: each line is the file's own text with
// its results/<file>:<line>. The short line and the glosses are authored and
// arrive from the server only when every anchor they summarise was found.
function renderVerdict() {
  const v = state.meta?.verdict || null;
  const box = $('verdict');
  if (box) box.dataset.state = v ? v.state : 'waiting';
  const shortText = v?.short?.[currentLang] || EM_DASH;
  setText($('verdict-short'), shortText);
  setText($('strip-verdict'), v ? shortText : '');
  const cells = $('verdict-cells');
  if (cells) {
    cells.textContent = '';
    for (const c of v?.cells || []) {
      const li = el('li');
      const cell = el('b', 'cell', c.cell);
      cell.dir = 'ltr';
      li.append(cell, el('span', 'gloss', c.gloss?.[currentLang] || ''));
      cells.appendChild(li);
    }
  }
  const lines = $('verdict-lines');
  if (lines) {
    lines.textContent = '';
    for (const line of v?.lines || []) {
      const fig = el('figure', 'quote');
      const pre = el('pre', '', line.text);
      pre.dir = 'ltr';
      const n = line.text.split('\n').length;
      const where = n > 1 ? `${line.line}-${line.line + n - 1}` : String(line.line);
      const cite = el('figcaption', '', t(currentLang, 'agents.verdict.source', { file: line.file, line: where }));
      cite.dir = 'ltr';
      fig.append(pre, cite);
      lines.appendChild(fig);
    }
  }
  const summary = $('verdict-more')?.querySelector('summary');
  const files = [...new Set((v?.lines || []).map(l => `results/${l.file}`))];
  setText(summary, files.length ? files.join(' · ') : EM_DASH);
  const scored = $('verdict-scored');
  if (!scored) return;
  scored.textContent = '';
  const m = state.meta;
  (m?.agents || []).forEach((agent, i) => {
    const status = !m.result_file ? t(currentLang, 'agents.verdict.no_result')
      : agent.scored === 'match' ? t(currentLang, 'agents.verdict.scored_match')
        : t(currentLang, 'agents.verdict.not_recorded');
    const li = el('li', LANES[i]);
    li.appendChild(el('i', 'lane-dot'));
    li.appendChild(el('span', '', `${t(currentLang, LANE_LABEL[i])} · ${status}`));
    const sha = el('code', '', `zip sha ${agent.zip_sha || EM_DASH}`);
    sha.dir = 'ltr';
    li.appendChild(sha);
    scored.appendChild(li);
  });
}

// Replayed at meta.dt, trained at meta.train_dt: said on the page, from meta.
function renderDtCaption() {
  const m = state.meta;
  if (!m) { setText($('dt-caption'), ''); return; }
  const train = [m.train_dt?.sighted, m.train_dt?.blind].map(num);
  if (train.some(v => v === null)) { setText($('dt-caption'), t(currentLang, 'agents.dt.not_recorded')); return; }
  if (train.every(v => v === m.dt)) { setText($('dt-caption'), t(currentLang, 'agents.dt.same')); return; }
  const shown = train[0] === train[1] ? String(train[0]) : `${train[0]} / ${train[1]}`;
  setText($('dt-caption'), t(currentLang, 'agents.dt.caption', { train_dt: shown }));
}

// ---------------------------------------------------------------- profile
function climbIndex(road) {
  const s = num(road?.climb_start_s);
  if (s === null) return null;
  return Math.min(road.grade_pct.length - 1, Math.max(0, Math.round(s / DT)));
}

// Whole route, x against height at VE x3, from the road the server built from
// the episode's own grade. One car marker: both cars are always at one place.
function drawProfile(road) {
  const host = $('profile');
  if (!host || !road) return;
  const p = profilePoints(road, { ve: PROFILE_VE, width: PROFILE_W });
  const height = Math.max(1, p.height);
  const Y = z => (height - z).toFixed(1);
  const line = p.points.map(([x, z], i) => `${i ? 'L' : 'M'}${x.toFixed(1)} ${Y(z)}`).join('');
  const ci = climbIndex(road);
  const climb = ci === null ? ''
    : `<line class="profile-climb" x1="${p.points[ci][0].toFixed(1)}" y1="${(-PROFILE_PAD).toFixed(1)}" x2="${p.points[ci][0].toFixed(1)}" y2="${height.toFixed(1)}"/>`;
  const ticks = (state.meta?.preview_s || []).map(() => '<line class="profile-tick" visibility="hidden"/>').join('');
  // x in km (design section 5, View 1): horizontal distance, every KM_STEP km.
  const kms = [];
  for (let km = 0; km * 1000 * p.sx <= PROFILE_W + 1e-6; km += KM_STEP) kms.push(km);
  const scale = kms.map(km => {
    const X = (km * 1000 * p.sx).toFixed(1);
    return `<line class="profile-km-tick" x1="${X}" y1="${height.toFixed(1)}" x2="${X}" y2="${(height + 8).toFixed(1)}"/>`;
  }).join('');
  host.innerHTML = `<svg viewBox="0 ${-PROFILE_PAD} ${PROFILE_W} ${height + 2 * PROFILE_PAD}" preserveAspectRatio="xMidYMid meet" aria-hidden="true">`
    + `<path class="profile-ground" d="${line}L${PROFILE_W} ${height}L0 ${height}Z"/>`
    + `<path class="profile-road" d="${line}"/>`
    + scale + climb + ticks
    + '<circle class="profile-car" r="7" cx="-40" cy="-40"/>'
    + '</svg>';
  const axis = el('div', 'profile-axis');
  axis.setAttribute('aria-hidden', 'true');
  for (const km of kms) {
    const label = el('span', 'profile-km');
    const frac = km * 1000 * p.sx / PROFILE_W;
    label.dataset.km = String(km);
    label.style.left = `${(frac * 100).toFixed(2)}%`;
    if (frac < 0.04) label.classList.add('start');
    else if (frac > 0.96) label.classList.add('end');
    axis.appendChild(label);
  }
  host.appendChild(axis);
  if (ci !== null) {
    const label = el('span', 'profile-climb-label');
    const frac = p.points[ci][0] / PROFILE_W;
    label.style.left = `${(frac * 100).toFixed(2)}%`;
    label.classList.toggle('flip', frac < 0.5);
    host.appendChild(label);
  }
  state.profile = {
    sx: p.sx, ve: p.ve, height,
    car: host.querySelector('.profile-car'),
    ticks: [...host.querySelectorAll('.profile-tick')],
  };
}

function renderProfileCaptions() {
  const road = state.road;
  const host = $('profile');
  setText($('profile-ve'), road ? t(currentLang, 'agents.profile.ve', { ve: PROFILE_VE }) : '');
  const rise = road ? t(currentLang, 'agents.profile.rise', {
    rise: fmtInt(road.rise_m), p: fmt(road.p_baro_kpa, 1), t: fmt(road.t_amb_c, 0),
  }) : '';
  setText($('rise-caption'), rise);
  if (host) host.setAttribute('aria-label', rise);
  host?.querySelectorAll('.profile-km').forEach(span => {
    setText(span, t(currentLang, 'agents.profile.km', { km: span.dataset.km }));
  });
  const label = host?.querySelector('.profile-climb-label');
  const ci = climbIndex(road);
  if (label && ci !== null) {
    setText(label, t(currentLang, 'agents.profile.climb', {
      start: fmt(road.climb_start_s, 0), grade: fmt(road.grade_pct[ci], 1),
    }));
  }
}

// The car marker and, for the sighted car only, a tick at each horizon it was
// given: x[min(k + int(h/dt), last)]. Four ticks, not a band -- it saw four numbers.
// Each tick is coloured by the grade there on the chase view's single-hue ramp
// (gradeRamp, 0 to 16 %), so the two views read the same way.
function moveProfile(at, showTicks = true) {
  const p = state.profile;
  if (!p) return;
  const X = x => (x * p.sx).toFixed(1);
  const Y = z => (p.height - z * p.sx * p.ve).toFixed(1);
  if (at.k < 0) {
    p.car.setAttribute('visibility', 'hidden');
    p.ticks.forEach(tick => tick.setAttribute('visibility', 'hidden'));
    return;
  }
  p.car.setAttribute('visibility', 'visible');
  p.car.setAttribute('cx', X(at.x_m));
  p.car.setAttribute('cy', Y(at.z_m));
  const marks = showTicks ? previewMarks(state.road, at.k, state.meta.preview_s, DT) : [];
  p.ticks.forEach((tick, i) => {
    const m = marks[i];
    if (!m) { tick.setAttribute('visibility', 'hidden'); return; }
    const y = p.height - m.z_m * p.sx * p.ve;
    tick.setAttribute('x1', X(m.x_m));
    tick.setAttribute('x2', X(m.x_m));
    tick.setAttribute('y1', (y - 18).toFixed(1));
    tick.setAttribute('y2', (y - 4).toFixed(1));
    const f = gradeRamp(m.grade_pct);
    tick.style.stroke = f === null ? 'var(--muted)'
      : `color-mix(in srgb, var(--agent-ramp-hi) ${(f * 100).toFixed(1)}%, var(--agent-ramp-lo))`;
    tick.setAttribute('visibility', 'visible');
  });
}

// ---------------------------------------------------------------- timeline
// Waiting: the viewer asked to play and the clock sits at the computed edge,
// either because play was pressed there (agent-view's waiting flag) or because
// playback caught up with the computation. More frames resume it either way.
function isWaiting() {
  const p = state.play;
  const c = p.clock;
  return p.waiting || (!p.userPaused && !state.done && !c.playing
    && state.frames.length > 0 && c.time >= c.duration - 1e-9);
}

// The track is the whole episode (meta.steps x meta.dt = 11:59); the clock's
// end is the COMPUTED end, and the uncomputed part is hatched.
function renderTimeline() {
  const m = state.meta;
  const end = m ? (num(m.steps) || 0) * (num(m.dt) || DT) : 0;
  const computed = state.frames.length * DT;
  setText($('duration'), formatTime(end));
  const seek = $('seek');
  if (seek) seek.max = String(end || 1);
  const fill = $('computed-fill');
  if (fill) fill.style.width = `${end > 0 ? Math.min(100, computed / end * 100) : 0}%`;
  const tick = $('climb-tick');
  const climb = num(state.road?.climb_start_s);
  if (tick) {
    tick.hidden = climb === null || !(end > 0);
    if (!tick.hidden) tick.style.left = `${(climb / end * 100).toFixed(2)}%`;
  }
  const note = $('computed-note');
  if (isWaiting()) setText(note, t(currentLang, 'agents.time.waiting'));
  else if (m && !state.done && state.frames.length) {
    setText(note, t(currentLang, 'agents.time.computed', { done: formatTime(computed), end: formatTime(end) }));
  } else setText(note, '');
}

function syncPlayButton() {
  const play = $('play');
  if (!play) return;
  const on = state.play.clock.playing || isWaiting();
  play.querySelector('use')?.setAttribute('href', on ? '#i-pause' : '#i-play');
  setText(play.querySelector('span'), t(currentLang, on ? 'transport.pause' : 'transport.play'));
  play.setAttribute('aria-label', t(currentLang, on ? 'transport.pause_aria' : 'transport.play_aria'));
}

// ---------------------------------------------------------------- per frame
function draw(time, force = false) {
  setText($('current-time'), formatTime(time));
  const seek = $('seek');
  if (seek && document.activeElement !== seek) seek.value = String(time);
  if (!state.road) return;
  const at = episodeAt(state.frames, state.road, time);
  moveProfile(at);
  if (force || at.k !== state.lastK) state.lastK = at.k;
}

function renderAll() {
  renderPicker();
  renderBadge();
  renderVerdict();
  renderDtCaption();
  renderProfileCaptions();
  renderTimeline();
  renderLoad();
  renderError();
  syncPlayButton();
  draw(state.play.clock.time, true);
}

// ---------------------------------------------------- theme and language
// Presentation only: switching either never changes a value on this page.
function applyTheme(name) {
  const theme = THEMES.includes(name) ? name : 'light';
  document.documentElement.dataset.theme = theme;
  const meta = document.querySelector('meta[name="theme-color"]');
  if (meta) {
    meta.setAttribute('content',
      getComputedStyle(document.documentElement).getPropertyValue('--bg').trim() || '#f4f3ed');
  }
  const button = $('theme-toggle');
  if (button) {
    button.title = t(currentLang, theme === 'dark' ? 'theme.to_light' : 'theme.to_dark');
    button.setAttribute('aria-pressed', String(theme === 'dark'));
    button.querySelector('use')?.setAttribute('href', theme === 'dark' ? '#i-sun' : '#i-moon');
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
    setText(button.querySelector('span'), other === 'en' ? 'EN' : 'AR');
  }
  renderAll();
  remember(STORE.lang, currentLang);
}

// ---------------------------------------------------------------- boot
function loop(now) {
  const clock = state.play.clock;
  const time = clock.tick(now);
  if (time !== state.drawnTime) { draw(time); state.drawnTime = time; }
  const on = clock.playing || isWaiting();
  if (on !== state.wasPlaying) { state.wasPlaying = on; syncPlayButton(); renderTimeline(); }
  requestAnimationFrame(loop);
}

function start() {
  $('play')?.addEventListener('click', () => {
    const now = performance.now();
    if (state.play.clock.playing || isWaiting()) pauseByUser(state.play, now);
    else playOrWait(state.play, state.frames.length * DT, state.done, now);
    syncPlayButton();
    renderTimeline();
  });
  $('restart')?.addEventListener('click', () => {
    const now = performance.now();
    pauseByUser(state.play, now);
    state.play.clock.seek(0, now);
    syncPlayButton();
    renderTimeline();
    draw(0, true);
  });
  $('seek')?.addEventListener('input', () => {
    const seek = $('seek');
    const now = performance.now();
    // Scrubbing clamps to what has been computed; nothing past it exists yet.
    const target = Math.min(Number(seek.value), state.play.clock.duration);
    state.play.clock.seek(target, now);
    if (Number(seek.value) !== target) seek.value = String(target);
    draw(state.play.clock.time, true);
  });
  $('rate')?.addEventListener('change', () => {
    state.play.clock.setRate(Number($('rate').value), performance.now());
  });
  $('compute')?.addEventListener('click', compute);
  $('theme-toggle')?.addEventListener('click', () => {
    applyTheme(document.documentElement.dataset.theme === 'dark' ? 'light' : 'dark');
  });
  $('lang-toggle')?.addEventListener('click', () => {
    applyLanguage(currentLang === 'ar' ? 'en' : 'ar');
  });
  applyTheme(recall(STORE.theme, THEMES,
    window.matchMedia?.('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'));
  applyLanguage(recall(STORE.lang, LANGS, DEFAULT_LANG));
  requestAnimationFrame(loop);
}

try {
  start();
} catch (err) {
  console.error(err);
  const message = err.message;
  showError(() => t(currentLang, 'agents.load.error', { message }));
}
