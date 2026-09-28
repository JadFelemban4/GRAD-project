// The /agents page shell, checked without a browser: every string the page
// names exists in BOTH languages, every t() call fills exactly the
// {placeholders} its string has, and the nav reads simulation, agents
// (active), monitor, review. A missing key renders as the key itself and a
// missing placeholder renders as "{percent}" -- both silently, on screen.
import test from 'node:test';
import assert from 'node:assert/strict';
import { existsSync, readFileSync } from 'node:fs';
import { STRINGS, LANGS } from './i18n.mjs';
import './agents-strings.mjs';
import { ACTIONS } from './agent-view.mjs';

const HTML = new URL('../agents.html', import.meta.url);
const PAGE = new URL('./agents.mjs', import.meta.url);

function read(url) {
  assert.ok(existsSync(url), `${url.pathname} does not exist`);
  return readFileSync(url, 'utf8');
}

const has = key => LANGS.every(lang => Object.prototype.hasOwnProperty.call(STRINGS[lang], key));
const slots = text => new Set([...text.matchAll(/\{(\w+)\}/g)].map(m => m[1]));

// Top-level property names of the object literal that opens at src[start].
// A scanner rather than a regex, because a value can hold calls, commas,
// brackets and strings of its own.
function objectKeys(src, start) {
  const parts = [];
  let depth = 0;
  let quote = null;
  let part = '';
  for (let i = start; i < src.length; i++) {
    const c = src[i];
    if (quote) {
      part += c;
      if (c === '\\') { part += src[i + 1]; i += 1; } else if (c === quote) quote = null;
      continue;
    }
    if (c === "'" || c === '"' || c === '`') { quote = c; part += c; continue; }
    if ('({['.includes(c)) { depth += 1; if (depth === 1) continue; }
    if (')}]'.includes(c)) { depth -= 1; if (depth === 0) { parts.push(part); break; } }
    if (c === ',' && depth === 1) { parts.push(part); part = ''; continue; }
    part += c;
  }
  return parts.map(p => p.trim()).filter(Boolean)
    .map(p => (p.match(/^([A-Za-z_$][\w$]*)/) || [])[1]);
}

// Every t(currentLang, '<literal key>' ...) call and the names it passes.
function tCalls(src) {
  const out = [];
  const head = /\bt\(\s*currentLang\s*,\s*'([^']+)'\s*/g;
  let m;
  while ((m = head.exec(src))) {
    let i = head.lastIndex;
    let names = [];
    if (src[i] === ',') {
      i += 1;
      while (/\s/.test(src[i])) i += 1;
      if (src[i] === '{') names = objectKeys(src, i);
    }
    out.push({ key: m[1], names });
  }
  return out;
}

test('every key agents.html names exists in both languages and carries no placeholder', () => {
  const html = read(HTML);
  const keys = [...new Set([...html.matchAll(/data-i18n(?:-aria|-title)?="([^"]+)"/g)].map(m => m[1]))];
  assert.ok(keys.length > 20, 'the key scan found almost nothing; the pattern has drifted');
  assert.deepEqual(keys.filter(k => !has(k)), []);
  // Markup has no way to fill a {slot}; a key with one would show it raw.
  assert.deepEqual(keys.filter(k => LANGS.some(lang => slots(STRINGS[lang][k]).size)), []);
});

test('every key agents.mjs names exists in both languages', () => {
  const src = read(PAGE);
  const calls = tCalls(src);
  assert.ok(calls.length > 20, 'the t() scan found almost nothing; the pattern has drifted');
  const literals = [...src.matchAll(/'((?:agents|nav|transport|theme|lang|rate|seed)\.[\w.]+)'/g)]
    .map(m => m[1]).filter(k => !k.endsWith('.mjs'));
  const keys = new Set([...calls.map(c => c.key), ...literals, ...ACTIONS.map(a => a.label)]);
  assert.deepEqual([...keys].filter(k => !has(k)), []);
});

test('each t() call fills exactly the placeholders of its string, in both languages', () => {
  const problems = [];
  for (const { key, names } of tCalls(read(PAGE))) {
    if (!has(key)) continue;   // reported by the test above
    const given = new Set(names);
    for (const lang of LANGS) {
      const want = slots(STRINGS[lang][key]);
      for (const s of want) if (!given.has(s)) problems.push(`${key} [${lang}] is never given {${s}}`);
      for (const g of given) if (!want.has(g)) problems.push(`${key} [${lang}] has no {${g}}`);
    }
  }
  assert.deepEqual(problems, []);
});

test('the nav reads simulation, agents (active), monitor, review', () => {
  const nav = read(HTML).match(/<nav[^>]*>([\s\S]*?)<\/nav>/);
  assert.ok(nav, 'agents.html has no <nav>');
  const links = [...nav[1].matchAll(/<a\b([^>]*)>/g)].map(m => m[1]);
  const attr = (a, name) => (a.match(new RegExp(`${name}="([^"]+)"`)) || [])[1];
  assert.deepEqual(links.map(a => attr(a, 'href')), ['/simulation', '/agents', '/', '/review']);
  assert.deepEqual(links.map(a => attr(a, 'data-i18n')),
    ['nav.simulation', 'nav.agents', 'nav.monitor', 'nav.review']);
  assert.deepEqual(links.map(a => /\bclass="[^"]*\bactive\b/.test(a)), [false, true, false, false]);
});

test('the honesty lines are in the markup itself, not only written by script', () => {
  const html = read(HTML);
  for (const [id, key] of [
    ['illustration-note', 'agents.illustration'],
    ['same-place-legend', 'agents.legend.same_place'],
    ['chase-caption', 'agents.scene.slope'],
    ['model-caveat', 'seed.model_output'],
    ['footer-index', 'agents.footer.index'],
    // M3 (design 7.7): the models panel's honesty lines, in the markup like
    // the others, so they are there the moment the panel is shown.
    ['models-not-thesis', 'agents.models.not_thesis'],
    ['models-claim', 'agents.models.claim'],
    ['models-levels', 'agents.models.levels'],
    ['model-jev-text', 'agents.models.jev.text'],
    ['model-laya-text', 'agents.models.laya.text'],
    ['model-laya-check', 'agents.models.laya.check'],
  ]) {
    const tag = html.match(new RegExp(`<[^>]*\\bid="${id}"[^>]*>`));
    assert.ok(tag, `#${id} is missing`);
    assert.ok(tag[0].includes(`data-i18n="${key}"`), `#${id} must carry data-i18n="${key}"`);
  }
  assert.match(html, /\bid="sim-badge"/);
});

test('every reading in the pause panel carries its own label', () => {
  const dl = read(HTML).match(/<dl class="car-readings">([\s\S]*?)<\/dl>/);
  assert.ok(dl, 'agents.html has no <dl class="car-readings">');
  const groups = [...dl[1].matchAll(/<div>([\s\S]*?)<\/div>/g)].map(m => m[1]);
  assert.equal(groups.length, 3, 'damage, turbine and torque');
  for (const group of groups) {
    assert.match(group, /^<dt\b[^>]*data-i18n="[^"]+"[^>]*>[^<]*<\/dt><dd\b/, `a reading without a label: ${group.slice(0, 60)}`);
  }
});

// «بلا تعديل» names the value at the zero tick, so it must stand ON the tick:
// under the end of the bar it labelled +4.0 (Arabic) or −8.0 (English) as "no
// change". agents.mjs gives the label the tick's own left %; these rules make
// that percentage mean the same place: an absolutely placed label, centred on
// its left edge, in a left-to-right box with the gauge's own side margins, in
// either page direction.
test('the zero-tick label is placed like the tick, in both page directions', () => {
  const css = read(new URL('./agents.css', import.meta.url));
  const rule = selector => {
    const m = css.match(new RegExp(`(?:^|\\})${selector.replace(/\./g, '\\.')}\\{([^}]*)\\}`, 'm'));
    assert.ok(m, `agents.css has no ${selector} rule`);
    return m[1];
  };
  const margin = decl => (decl.match(/margin:([^;]+)/) || [])[1]?.trim().split(/\s+/);
  const gauge = rule('.gauge');
  const ends = rule('.gauge-ends');
  const label = rule('.tick-label');
  assert.match(gauge, /direction:ltr/);
  assert.match(ends, /direction:ltr/, 'the label box must not flip with the page direction');
  assert.match(ends, /position:relative/);
  assert.equal(margin(ends)[1], margin(gauge)[1], 'the label box and the gauge must share their side margins');
  assert.match(label, /position:absolute/);
  assert.match(label, /translateX\(-50%\)/, 'the label must be centred on the tick');
  assert.doesNotMatch(css, /html\[dir=ltr\][^{]*\.(?:gauge-ends|tick-label)/, 'no per-direction override of the label box');
});

test('the profile ticks and the chase posts share one ramp, in both themes', () => {
  const css = read(new URL('./agents.css', import.meta.url));
  const scene = read(new URL('./agent-scene.mjs', import.meta.url));
  const ramp = scene.match(/const RAMP = \{[\s\S]*?\n\};/);
  assert.ok(ramp, 'agent-scene.mjs has no RAMP table');
  const tokens = [...css.matchAll(/--agent-ramp-(?:lo|hi):#([0-9a-f]{6})/g)].map(m => m[1]);
  assert.equal(tokens.length, 6, 'lo and hi in each of the three theme blocks');
  for (const hex of tokens) assert.ok(ramp[0].includes(`0x${hex}`), `#${hex} is not in agent-scene.mjs's RAMP`);
});

// M3 (design 7.2, the agents.css row). Below 1100 px .agents-layout is one
// flex column with align-items:start, so a panel hugs the start edge unless it
// stretches; the models panel comes after the pause panel there; its two
// columns fold into one on a phone; and ten fast taps on the footer label
// must not zoom the page.
test('the models panel stretches, comes after the pause panel below 1100 px, and the footer label never zooms', () => {
  const css = read(new URL('./agents.css', import.meta.url));
  assert.match(css, /\.pause-panel,\.models-panel\{background:var\(--paper\)/, 'the models panel is a card like the pause panel');
  assert.match(css, /(?:^|\})\.models-panel\{align-self:stretch\}/m);
  const narrow = css.match(/@media\(max-width:1099px\)\{([\s\S]*?)\n\}/);
  assert.ok(narrow, 'agents.css has no <1100 px block');
  const order = name => Number((narrow[1].match(new RegExp(`\\.${name}\\{order:(\\d+)\\}`)) || [])[1]);
  assert.equal(order('models-panel'), 7);
  assert.ok(order('models-panel') > order('pause-panel'), 'the models panel follows the pause panel');
  assert.match(css, /@media\(max-width:760px\)\{\s*\.models-columns\{grid-template-columns:1fr\}/);
  assert.match(css, /(?:^|\})\.footer-index\{[^}]*touch-action:manipulation/m);
});
