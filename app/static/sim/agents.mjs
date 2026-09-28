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
// M2: the picker WORKS. At boot the page loads GET /api/agents/catalog, and
// agent-picker.mjs decides what the three selects offer. The page opens with
// NOTHING selected unless the address names a selection the catalog allows,
// never a default pair. Every change of a select replaces the address (never a
// new history entry) and clears the episode on screen. Nothing computes until
// «احسب» is pressed. Nothing is stored in the browser except the lab's own
// theme and language preferences.
import './agents-strings.mjs';
import { t, LANGS, DEFAULT_LANG, resolveLang, applyTranslations } from './i18n.mjs';
import { PlaybackClock, formatTime } from './playback.mjs';
import {
  DT, PROFILE_VE, appendFrames, createPlayState, playOrWait,
  pauseByUser, resumeIfStalled, settleDone, episodeAt, profilePoints, previewMarks, gradeRamp,
  ACTIONS, M_PER_UNIT, createEpisodeRoad, gaugeFraction, commandPhysical, laneStoppedAt,
} from './agent-view.mjs';
import {
  NOTHING, parsePickerQuery, experimentOf, pairOf, resolveSelection, choose, selectionSearch,
  computeState, experimentOptions, pairOptions, episodeOptions, pairQualifier, sameRoadNote,
  refusedPairs, scoredKey,
} from './agent-picker.mjs';

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

// The chase view is loaded on demand (mountChase) and may never exist: when
// Three.js or WebGL fails, every other surface of the page still renders.
let chase = null;
let chaseToken = 0;
// The blind car's label, by protocol. M2 gives Phase D's blind car its own
// ("may have memorised the road", PHASE_D_RESULT.txt:33-37) as one more row.
const BLIND_LABEL = { d2: 'agents.car.blind', 'phase-d': 'agents.car.blind' };

const state = {
  catalog: null,   // GET /api/agents/catalog, once it has arrived
  bootQuery: parsePickerQuery(window.location.search),
  sel: { ...NOTHING },   // what the three selects name: { runs, seed, ep }
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
  rows: [],        // the five action rows of the pause panel, built per meta
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
const sameSel = (a, b) => a.runs === b.runs && a.seed === b.seed && a.ep === b.ep;

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
  setText($('load-detail'), state.sel.runs === null ? '' : keyOf(state.sel));
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
  const q = state.sel;
  const params = new URLSearchParams({
    runs: q.runs, seed: String(q.seed), ep: String(q.ep), since: String(since),
  });
  if (preempt) params.set('preempt', '1');
  return `/api/agents/episode?${params}`;
}

// «احسب». The one request that carries a person's decision sends preempt=1;
// every poll after it waits its turn (app.replay's rule, kept here).
function compute() {
  if (!computeState(state.catalog, state.sel).ok) return;
  state.loadToken += 1;
  const token = state.loadToken;
  const now = performance.now();
  pauseByUser(state.play, now);
  state.play = createPlayState(new PlaybackClock(0));
  state.play.clock.setRate(Number($('rate')?.value) || 1, now);
  if (state.metaKey !== keyOf(state.sel)) { state.meta = null; state.road = null; }
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
  renderDevice();
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
  // Not awaited: the rest of the page must not wait for Three.js. An error
  // after the scene exists is logged as itself (mountChase).
  mountChase(road).catch(err => console.error(err));
  renderAll();
}

// ---------------------------------------------------------------- picker
// What the three selects name, read from the catalog. The verdict box follows
// the chosen experiment even before «احسب»; after it, the episode's own meta
// is only the fallback (the two always agree: the route reads one catalog).
function currentExperiment() {
  return experimentOf(state.catalog, state.sel.runs);
}
function currentPair() {
  return pairOf(currentExperiment(), state.sel.seed);
}
function currentVerdict() {
  return currentExperiment()?.verdict ?? state.meta?.verdict ?? null;
}

// The <option>s and the refused list are rebuilt only when their text
// changed, so a select is never rebuilt under the viewer's pointer by a poll
// or a redraw, and an open list does not close.
const drawn = new WeakMap();
function fillSelect(select, options, value) {
  if (!select) return;
  const signature = JSON.stringify(options);
  if (drawn.get(select) !== signature) {
    drawn.set(select, signature);
    select.textContent = '';
    for (const o of options) {
      const node = el('option', '', o.text);
      node.value = o.value;
      node.disabled = o.disabled;
      select.appendChild(node);
    }
  }
  select.value = value === null ? '' : String(value);
}

// Every pair that cannot run, in every experiment, with EVERY problem the
// server found (design section 8, "listed and disabled with reason and
// fields"): both arms, and each stored and live field of a plant mismatch
// (agent-picker.refusedPairs). A greyed option has room for the first
// problem only.
function renderRefused() {
  const box = $('pick-refused');
  if (!box) return;
  const refused = refusedPairs(state.catalog);
  box.hidden = !refused.length;
  const signature = JSON.stringify([currentLang, refused]);
  if (drawn.get(box) === signature) return;
  drawn.set(box, signature);
  box.textContent = '';
  if (!refused.length) return;
  box.appendChild(el('summary', '', t(currentLang, 'agents.pick.refused_summary', { n: refused.length })));
  for (const r of refused) {
    const item = el('div', 'refused-pair');
    item.appendChild(el('b', '', t(currentLang, 'agents.pick.refused_pair', { name: r.name, seed: r.seed })));
    // The server's own words, read left to right: bullets and indent on the left.
    const list = el('ul');
    list.dir = 'ltr';
    for (const problem of r.problems) list.appendChild(el('li', '', String(problem)));
    item.appendChild(list);
    box.appendChild(item);
  }
}

function renderPicker() {
  const catalog = state.catalog;
  const sel = state.sel;
  const experiment = currentExperiment();
  const pair = currentPair();
  const episodes = episodeOptions(catalog, pair, currentLang);
  fillSelect($('pick-experiment'), experimentOptions(catalog, currentLang), sel.runs);
  fillSelect($('pick-pair'), pairOptions(experiment, currentLang), sel.seed);
  fillSelect($('pick-episode'), episodes, sel.ep);
  const enable = (id, on) => { const node = $(id); if (node) node.disabled = !on; };
  enable('pick-experiment', Boolean(catalog));
  enable('pick-pair', Boolean(experiment));
  enable('pick-episode', Boolean(pair));
  setText($('pick-pair-note'), pairQualifier(experiment, currentLang));
  setText($('pick-episode-note'), sameRoadNote(catalog, experiment, currentLang));
  const can = computeState(catalog, sel);
  enable('compute', can.ok);
  renderRefused();
  const note = $('pick-note');
  if (!note) return;
  note.textContent = '';
  // Without stable-baselines3 nothing can be computed (design section 4,
  // Runnability). Said as soon as the catalog arrives, not after three
  // choices; the pairs stay selectable, so their verdicts and table rows can
  // still be read.
  if (catalog && !catalog.sb3) note.appendChild(el('span', 'pick-reason pick-warning', t(currentLang, 'agents.load.no_sb3')));
  // The select may truncate on a narrow screen; the chosen episode and its
  // weights must stay legible, so they are spelled out here as well.
  const chosen = episodes.find(o => sel.ep !== null && o.value === String(sel.ep));
  if (chosen) note.appendChild(el('span', '', chosen.text));
  (pair?.agents || []).forEach((agent, i) => {
    const line = el('span', LANES[i]);
    line.appendChild(el('i', 'lane-dot'));
    line.appendChild(el('span', '', `${t(currentLang, LANE_LABEL[i])} · ${t(currentLang, 'agents.pick.budget', { budget: budgetSteps(agent.budget_line) })}`));
    note.appendChild(line);
  });
  // What is still to choose; the missing stable-baselines3 is said once, above.
  if (!can.ok && can.reason !== 'agents.load.no_sb3') note.appendChild(el('span', 'pick-reason', t(currentLang, can.reason)));
}

// Everything on screen that belongs to the episode last computed goes, and a
// late response for it is dropped: loadToken is what poll() checks after every
// await, and chaseToken is what mountChase() checks after its import.
function clearEpisode() {
  state.loadToken += 1;
  const now = performance.now();
  pauseByUser(state.play, now);
  state.play = createPlayState(new PlaybackClock(0));
  state.play.clock.setRate(Number($('rate')?.value) || 1, now);
  state.frames = [];
  state.meta = null;
  state.metaKey = null;
  state.road = null;
  state.done = false;
  state.device = null;
  state.versions = null;
  state.lastK = -2;
  state.drawnTime = -1;
  const profile = $('profile');
  if (profile) profile.textContent = '';
  state.profile = null;
  chaseToken += 1;
  chase?.dispose();
  chase = null;
  const scene = $('chase');
  if (scene) scene.textContent = '';
  showLoad(null);
  showError(null);
  const prompt = $('scene-prompt');
  if (prompt) prompt.hidden = false;
  setControlsEnabled(false);
  renderPanel(-1);
}

// A viewer changed one select. choose() says what that selects; a choice that
// changes nothing (the same value, or a greyed option) only redraws the picker.
function onPick(level, select) {
  if (!state.catalog || !select) return;
  const next = choose(state.catalog, state.sel, level, select.value);
  if (sameSel(next, state.sel)) { renderPicker(); return; }
  clearEpisode();
  state.sel = next;
  window.history?.replaceState?.(null, '', `/agents${selectionSearch(next)}`);
  renderAll();
}

// The catalog, once, at boot. It never starts a computation.
async function loadCatalog() {
  showError(null);
  let res;
  let body = null;
  try {
    res = await fetch('/api/agents/catalog', { headers: { Accept: 'application/json' }, cache: 'no-store' });
    body = await res.json().catch(() => null);
  } catch (err) {
    showError(() => t(currentLang, 'agents.pick.catalog_error', { message: t(currentLang, 'agents.load.server_down') }),
      { retry: loadCatalog });
    return;
  }
  if (res.status !== 200 || !body || !Array.isArray(body.experiments)) {
    const message = `HTTP ${res.status}`;
    showError(() => t(currentLang, 'agents.pick.catalog_error', { message }), { retry: loadCatalog });
    return;
  }
  state.catalog = body;
  state.sel = resolveSelection(body, state.bootQuery);
  // The address never names more than is selected. It is compared as TEXT:
  // parsePickerQuery has already dropped a malformed level (runs_C4, seed=5abc,
  // ep=21), so comparing selections would leave such an address as it was.
  const search = selectionSearch(state.sel);
  if (window.location.search !== search) window.history?.replaceState?.(null, '', `/agents${search}`);
  renderAll();
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
  const v = currentVerdict();
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
  // The chosen pair's agents from the catalog, so the box reads before «احسب».
  const agents = state.meta?.agents ?? currentPair()?.agents ?? [];
  const resultFile = state.meta ? state.meta.result_file : currentPair()?.result_file;
  agents.forEach((agent, i) => {
    // agent-picker.scoredKey: match, not recorded, mismatch or no result file;
    // null when the sha check never ran, and then nothing is claimed.
    const key = scoredKey(agent.scored, resultFile);
    const status = key ? t(currentLang, key) : EM_DASH;
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

// ---------------------------------------------------------------- chase view
// Lane `lane` of a frame, or null. A lane that diverged is null from that
// step on (design 3.2), so every read of a car goes through here.
function carOf(frame, lane) {
  return frame?.cars?.[lane] ?? null;
}

function laneColours() {
  const css = getComputedStyle(document.documentElement);
  // The fallbacks only matter if agents.css failed to load.
  return {
    sighted: css.getPropertyValue('--agent-sighted').trim() || '#2f6db0',
    blind: css.getPropertyValue('--agent-blind').trim() || '#b5761c',
  };
}

// Loaded by DYNAMIC import, never a static one: app/static/vendor/ is
// gitignored and exists only after app\start-simulation.ps1, and a failed
// static import of Three.js would take the whole module graph -- verdict,
// badge, dt caption, profile, panel -- down with it.
//
// The try holds ONLY the import and createChaseScene, the two steps that fail
// when Three.js or WebGL is missing, so only they show the WebGL message. A
// scene that fails half-built disposes its own stage before it throws
// (agent-scene.mjs), and the canvas it left in the host is cleared here. An
// error after the scene exists -- in setTheme, or in the pause panel that
// draw() renders -- is not a WebGL failure: it reaches applyMeta's catch and
// the console as itself.
async function mountChase(road) {
  const host = $('chase');
  if (!host || !road) return;
  chaseToken += 1;
  const token = chaseToken;
  chase?.dispose();
  chase = null;
  host.textContent = '';
  let created;
  try {
    const { createChaseScene } = await import('./agent-scene.mjs');
    if (token !== chaseToken) return;
    created = createChaseScene(host, createEpisodeRoad(road, M_PER_UNIT), laneColours());
  } catch (err) {
    console.error(err);
    if (token !== chaseToken) return;
    host.textContent = '';
    host.appendChild(el('p', 'webgl-error', t(currentLang, 'agents.scene.webgl_error')));
    return;
  }
  chase = created;
  chase.setTheme(document.documentElement.dataset.theme || 'light', laneColours());
  draw(state.play.clock.time, true);
}

function renderLaneLabels() {
  const m = state.meta;
  setText($('lane-sighted-label'), m ? t(currentLang, 'agents.car.sighted') : '');
  setText($('lane-blind-label'), m ? t(currentLang, BLIND_LABEL[m.protocol] || 'agents.car.blind') : '');
}

// ---------------------------------------------------------------- pause panel
// The APPLIED action (env.prev_act after rescale, slew limit and bounds) in
// its own unit: trims signed, duties as fractions.
function fmtAction(i, v) {
  const n = num(v);
  if (n === null) return EM_DASH;
  const key = ACTIONS[i].key;
  const text = n.toFixed(ACTIONS[i].digits);
  if (key === 'fan' || key === 'pump') return text;
  return n > 0 ? `+${text}` : text.replace('-', '\u2212');
}

// The note under each duty row, by device. The modelled computer schedules the
// fan (engine_env.py:265); the pump runs at thermal.py's default 1.0 throughout
// (engine_env.py:764-765). The results' "baseline ECU" row runs both at a
// constant 1.0 (evaluate.py:347).
const DUTY_NOTE = { fan: 'agents.action.tick_fan', pump: 'agents.action.tick_pump' };

// Five rows, built once per meta and language: a bar from lo to hi, a tick at
// the neutral value, one dot per car. renderActions only moves the dots.
function buildActionRows() {
  const host = $('actions');
  state.rows = [];
  if (!host) return;
  host.textContent = '';
  const act = state.meta?.act;
  if (!act) return;
  ACTIONS.forEach((action, i) => {
    const duty = action.key === 'fan' || action.key === 'pump';
    const row = el('div', 'action-row');
    const head = el('div', 'action-head');
    head.appendChild(el('span', 'action-label', t(currentLang, action.label)));
    if (action.unit) {
      const unit = el('span', 'action-unit', action.unit);
      unit.dir = 'ltr';
      head.appendChild(unit);
    }
    const gauge = el('div', 'gauge');
    const tick = el('i', 'gauge-tick');
    const neutral = gaugeFraction(act.neutral_phys[i], act.lo[i], act.hi[i]);
    tick.style.left = `${((neutral ?? 0) * 100).toFixed(2)}%`;
    gauge.appendChild(tick);
    const dots = LANES.map(lane => {
      const dot = el('i', `gauge-dot ${lane}`);
      dot.hidden = true;
      gauge.appendChild(dot);
      return dot;
    });
    const ends = el('div', 'gauge-ends');
    ends.append(el('span', '', fmtAction(i, act.lo[i])), el('span', '', fmtAction(i, act.hi[i])));
    // A trim's tick is at 0, and «بلا تعديل» names THAT value, so it stands on
    // the tick: the same left % in a box with the gauge's own geometry
    // (agents.css .gauge-ends). A duty row's tick is its end, 1.0, and its
    // note is a sentence about its own device, under the bar.
    let note = null;
    if (duty) note = el('p', 'tick-note', t(currentLang, DUTY_NOTE[action.key]));
    else {
      const label = el('span', 'tick-label', t(currentLang, 'agents.action.tick_trim'));
      label.style.left = tick.style.left;
      ends.appendChild(label);
    }
    const values = el('div', 'action-values');
    const cells = LANES.map(lane => {
      const cell = el('div', `car-value ${lane}`);
      const value = el('b', 'value', EM_DASH);
      value.dir = 'ltr';
      const held = el('small', 'held-line');
      held.hidden = true;
      const map = el('small', 'map-line');
      map.hidden = true;
      cell.append(el('i', 'lane-dot'), value, held, map);
      values.appendChild(cell);
      return { value, held, map };
    });
    row.append(head, gauge, ends, ...(note ? [note] : []), values);
    host.appendChild(row);
    state.rows.push({ dots, cells });
  });
}

function renderActions(frame) {
  const act = state.meta?.act;
  if (!act) return;
  state.rows.forEach((row, i) => {
    row.cells.forEach((cell, j) => {
      const car = carOf(frame, j);
      const dot = row.dots[j];
      if (!car) {
        setText(cell.value, EM_DASH);
        cell.held.hidden = true;
        cell.map.hidden = true;
        dot.hidden = true;
        return;
      }
      const applied = car.act?.[i];
      setText(cell.value, fmtAction(i, applied));
      const f = gaugeFraction(applied, act.lo[i], act.hi[i]);
      dot.hidden = f === null;
      if (f !== null) dot.style.left = `${(f * 100).toFixed(2)}%`;
      // The command appears only where the rate limit held it back, and only
      // when both values exist: a diverged step sends five nulls for cmd and
      // act with held all true (NaN != NaN), and there is nothing to show.
      const command = Array.isArray(car.cmd) ? commandPhysical(car.cmd, act.lo, act.hi)[i] : null;
      const held = Boolean(car.held?.[i]) && num(applied) !== null && num(command) !== null;
      cell.held.hidden = !held;
      if (held) setText(cell.held, t(currentLang, 'agents.action.held', { x: fmtAction(i, command) }));
      // Row 2 offsets the CEILING of the agent's own pressure loop; its own
      // manifold pressure is what shows whether that ceiling was reached.
      cell.map.hidden = ACTIONS[i].key !== 'boost';
      if (!cell.map.hidden) setText(cell.map, t(currentLang, 'agents.action.map', { map: fmt(car.map_kpa, 1) }));
    });
  });
}

// What each car was given: the sighted car's four horizons from meta.preview_s
// (engine_env.PREVIEW_S), the blind car's real inputs -- zeros, read from the
// frame rather than written here.
function renderSeen(frame) {
  const horizons = state.meta?.preview_s || [];
  const sighted = carOf(frame, 0);
  const blind = carOf(frame, 1);
  setText($('seen-sighted'), sighted
    ? horizons.map((h, i) => t(currentLang, 'agents.seen.item', { h, pct: fmt(sighted.preview_pct[i], 1) })).join(' · ')
    : '');
  const zeros = blind ? blind.preview_pct.map(v => (v === 0 ? '0' : fmt(v, 1))).join(' · ') : '';
  setText($('seen-blind'), blind ? t(currentLang, 'agents.seen.blind', { zeros }) : '');
}

// The limit arrives as 849.9 (TURB_PROTECT_K - 273.15, one decimal); the
// results files and the documents say 850, so it is shown with none. The unit
// is the language's own, «°م» in Arabic as on the badge, and an Arabic unit
// needs a right-to-left box or the line reorders into "700 °م° 850 / م".
function renderReadings(frame) {
  const limit = state.meta?.limits?.turb_c;
  const outputs = [
    { damage: $('damage-sighted'), turb: $('turb-sighted'), torque: $('torque-sighted') },
    { damage: $('damage-blind'), turb: $('turb-blind'), torque: $('torque-blind') },
  ];
  outputs.forEach((out, j) => {
    const car = carOf(frame, j);
    setText(out.damage, car ? fmt(car.damage, 1) : EM_DASH);
    if (out.turb) out.turb.dir = currentLang === 'ar' ? 'rtl' : 'ltr';
    setText(out.turb, car
      ? t(currentLang, 'agents.turbine.reading', { turb: fmt(car.turb_c, 0), limit: fmt(limit, 0) })
      : EM_DASH);
    setText(out.torque, car ? t(currentLang, 'agents.torque.label', {
      delivered: fmt(car.torque_nm, 0), requested: fmt(car.torque_req_nm, 0),
    }) : EM_DASH);
  });
}

// CPU and CUDA give different episodes (recon section 2), so the device and
// the versions are shown, and a non-CUDA run says so.
function renderDevice() {
  const line = $('device-line');
  if (line) {
    const v = state.versions || {};
    const signature = `${state.device}|${v.torch}|${v.sb3}|${currentLang}`;
    if (line.dataset.signature !== signature) {
      line.dataset.signature = signature;
      line.textContent = '';
      if (state.device) {
        line.appendChild(el('span', '', t(currentLang, 'agents.device.line', {
          device: state.device, torch: v.torch || EM_DASH, sb3: v.sb3 || EM_DASH,
        })));
        if (!String(state.device).startsWith('cuda')) {
          line.appendChild(el('strong', 'device-warning', t(currentLang, 'agents.device.warning')));
        }
      }
    }
  }
  const time = state.meta?.fingerprint_taken;
  setText($('fingerprint-taken'), time ? t(currentLang, 'agents.fingerprint_taken', { time }) : '');
}

function renderStopped() {
  const node = $('lane-stopped');
  if (!node) return;
  const parts = LANE_LABEL.map((label, j) => {
    const k = laneStoppedAt(state.frames, j);
    return k === null ? null : `${t(currentLang, label)}: ${t(currentLang, 'agents.lane.stopped', { k })}`;
  }).filter(Boolean);
  node.hidden = !parts.length;
  setText(node, parts.join(' · '));
}

// The decision applied from second k to k+1. Called only when k changes, so
// it holds still while paused. Nothing here compares the two cars.
function renderPanel(k) {
  const frame = k >= 0 ? state.frames[k] || null : null;
  const road = state.road;
  setText($('pause-heading'), frame ? t(currentLang, 'agents.pause.heading', { k, k1: k + 1 }) : EM_DASH);
  setText($('grade-now'), frame && road
    ? t(currentLang, 'agents.pause.grade_now', { grade: fmt(road.grade_pct[k], 1) }) : '');
  const w = state.meta?.episode?.weights;
  setText($('weights-line'), w
    ? t(currentLang, 'agents.pause.weights', { w0: fmt(w[0], 2), w1: fmt(w[1], 2), w2: fmt(w[2], 2) }) : '');
  renderActions(frame);
  renderSeen(frame);
  renderReadings(frame);
  renderStopped();
}

// ---------------------------------------------------------------- per frame
function draw(time, force = false) {
  setText($('current-time'), formatTime(time));
  const seek = $('seek');
  if (seek && document.activeElement !== seek) seek.value = String(time);
  if (!state.road) return;
  const at = episodeAt(state.frames, state.road, time);
  const sighted = carOf(at.frame, 0);
  moveProfile(at, Boolean(sighted));
  if (chase) {
    // Four markers where the sighted car's horizons land, coloured by the
    // grade it was given there. Both cars share one distance: the scenario
    // imposes the speed.
    const marks = sighted
      ? previewMarks(state.road, at.k, state.meta.preview_s, DT)
        .map((m, i) => ({ s_m: m.s_m, grade_pct: sighted.preview_pct[i] }))
      : [];
    chase.update({ distance_m: at.s_m, marks });
  }
  if (force || at.k !== state.lastK) {
    state.lastK = at.k;
    renderPanel(at.k);
  }
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
  renderLaneLabels();
  buildActionRows();
  renderDevice();
  setText($('chase')?.querySelector('.webgl-error'), t(currentLang, 'agents.scene.webgl_error'));
  syncPlayButton();
  draw(state.play.clock.time, true);
}

// ---------------------------------------------------- theme and language
// Presentation only: switching either never changes a value on this page.
function applyTheme(name) {
  const theme = THEMES.includes(name) ? name : 'light';
  document.documentElement.dataset.theme = theme;
  chase?.setTheme(theme, laneColours());
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
  $('pick-experiment')?.addEventListener('change', () => onPick('runs', $('pick-experiment')));
  $('pick-pair')?.addEventListener('change', () => onPick('seed', $('pick-pair')));
  $('pick-episode')?.addEventListener('change', () => onPick('ep', $('pick-episode')));
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
  loadCatalog().catch(err => console.error(err));
}

try {
  start();
} catch (err) {
  console.error(err);
  const message = err.message;
  showError(() => t(currentLang, 'agents.load.error', { message }));
}
