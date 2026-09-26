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

test('the profile ticks and the chase posts share one ramp, in both themes', () => {
  const css = read(new URL('./agents.css', import.meta.url));
  const scene = read(new URL('./agent-scene.mjs', import.meta.url));
  const ramp = scene.match(/const RAMP = \{[\s\S]*?\n\};/);
  assert.ok(ramp, 'agent-scene.mjs has no RAMP table');
  const tokens = [...css.matchAll(/--agent-ramp-(?:lo|hi):#([0-9a-f]{6})/g)].map(m => m[1]);
  assert.equal(tokens.length, 6, 'lo and hi in each of the three theme blocks');
  for (const hex of tokens) assert.ok(ramp[0].includes(`0x${hex}`), `#${hex} is not in agent-scene.mjs's RAMP`);
});
