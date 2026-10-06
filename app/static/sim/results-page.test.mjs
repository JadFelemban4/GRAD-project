// The /results page shell, checked without a browser: every stylesheet and
// module it names exists, every id results.mjs reads is declared once, every
// import resolves, the tab's own modules carry one version query and the
// lab's shared modules none (a second query would load a second copy of
// results-strings.mjs, whose merge then refuses), every key the markup and
// the page name exists in both languages, and the nav reads simulation,
// agents, results (active), monitor, review. The lab was dead for a day once
// because one module did not exist; these are the checks that catch it.
import test from 'node:test';
import assert from 'node:assert/strict';
import { existsSync, readFileSync } from 'node:fs';
import { STRINGS, LANGS } from './i18n.mjs';
import './results-strings.mjs?v=R1a';

const STATIC = new URL('../', import.meta.url);
const HTML = new URL('../results.html', import.meta.url);
const VERSION = 'v=R1a';
const OWN = ['results.mjs', 'results-view.mjs', 'results-charts.mjs', 'results-format.mjs',
  'results-strings.mjs', 'charts-lib.mjs'];
const SHARED = ['i18n.mjs', 'agent-picker.mjs'];
const IDS = ['error', 'built', 'warnings', 'summary', 'summary-rows', 'sections', 'not-read', 'not-read-list',
  'theme-toggle', 'lang-toggle', 'footer-index'];

function read(url) {
  assert.ok(existsSync(url), `${url.pathname} does not exist`);
  return readFileSync(url, 'utf8');
}
const has = key => LANGS.every(lang => Object.prototype.hasOwnProperty.call(STRINGS[lang], key));
const slots = text => new Set([...text.matchAll(/\{(\w+)\}/g)].map(m => m[1]));
// Every relative import of a module: static, side-effect and dynamic.
const importsOf = src => [
  ...[...src.matchAll(/\bfrom\s+'(\.\/[^']+)'/g)].map(m => m[1]),
  ...[...src.matchAll(/^import\s+'(\.\/[^']+)'/gm)].map(m => m[1]),
  ...[...src.matchAll(/\bimport\(\s*'(\.\/[^']+)'\s*\)/g)].map(m => m[1]),
];
const split = spec => {
  const [path, query = ''] = spec.split('?');
  return { file: path.slice(2), query };
};

test('every stylesheet and script results.html names exists, the tab\'s own with the version query', () => {
  const html = read(HTML);
  const links = [...html.matchAll(/<link[^>]+href="\/static\/([^"]+)"/g)].map(m => m[1]);
  const scripts = [...html.matchAll(/<script[^>]+src="\/static\/([^"]+)"/g)].map(m => m[1]);
  assert.deepEqual(links, ['sim/style.css', 'sim/agents.css', `sim/results.css?${VERSION}`]);
  assert.deepEqual(scripts, [`sim/results.mjs?${VERSION}`]);
  for (const ref of [...links, ...scripts]) {
    assert.ok(existsSync(new URL(ref.split('?')[0], STATIC)), `${ref} is referenced by the page and does not exist`);
  }
  assert.doesNotMatch(html, /type="importmap"/, 'this page loads no Three.js, so it carries no import map');
});

test('ids are declared once, and every id results.mjs reads is declared', () => {
  const html = read(HTML);
  const ids = [...html.matchAll(/\sid="([^"]+)"/g)].map(m => m[1]);
  assert.equal(ids.length, new Set(ids).size, 'an id is declared twice in results.html');
  for (const id of IDS) assert.ok(ids.includes(id), `#${id} is missing from results.html`);
  const used = new Set([...read(new URL('./results.mjs', import.meta.url)).matchAll(/\$\('([^']+)'\)/g)].map(m => m[1]));
  assert.ok(used.size > 5, 'the id scan found almost nothing; the pattern has drifted');
  assert.deepEqual([...used].filter(id => !ids.includes(id)), []);
  for (const symbol of ['i-sun', 'i-moon']) assert.ok(ids.includes(symbol), `#${symbol} is not in the icon library`);
});

test('every import of the tab\'s modules resolves: its own with ?v=R1a, the shared ones bare', () => {
  for (const name of OWN) {
    const src = read(new URL(`./${name}`, import.meta.url));
    for (const spec of importsOf(src)) {
      const { file, query } = split(spec);
      assert.ok(existsSync(new URL(`./${file}`, import.meta.url)), `${name} imports missing ${spec}`);
      if (OWN.includes(file)) assert.equal(query, VERSION, `${name} imports ${spec}: the tab's modules carry ?${VERSION}`);
      else if (SHARED.includes(file)) assert.equal(query, '', `${name} imports ${spec}: a shared lab module carries no query`);
      else assert.fail(`${name} imports ${spec}, which is neither the tab's nor a shared lab module`);
    }
  }
  const page = importsOf(read(new URL('./results.mjs', import.meta.url))).map(s => split(s).file);
  for (const name of ['results-strings.mjs', 'results-view.mjs', 'results-charts.mjs', 'charts-lib.mjs', 'i18n.mjs']) {
    assert.ok(page.includes(name), `results.mjs does not import ${name}`);
  }
});

test('every key results.html names exists in both languages, carries no placeholder, and the markup holds its Arabic', () => {
  const html = read(HTML);
  const keys = [...new Set([...html.matchAll(/data-i18n(?:-aria|-title)?="([^"]+)"/g)].map(m => m[1]))];
  assert.ok(keys.length > 15, 'the key scan found almost nothing; the pattern has drifted');
  assert.deepEqual(keys.filter(k => !has(k)), []);
  assert.deepEqual(keys.filter(k => LANGS.some(lang => slots(STRINGS[lang][k]).size)), []);
  // Before the script runs the page reads in Arabic: each marked element's own
  // text is its Arabic string (character references decoded).
  const decode = s => s.replace(/&#x([0-9a-f]+);/gi, (_, h) => String.fromCodePoint(parseInt(h, 16)));
  const marked = [...html.matchAll(/<(\w+)\b[^>]*\bdata-i18n="([^"]+)"[^>]*>([^<]*)<\/\1>/g)];
  assert.ok(marked.length > 15, 'the text scan found almost nothing; the pattern has drifted');
  for (const [, , key, text] of marked) assert.equal(decode(text), STRINGS.ar[key], `the markup's text for ${key}`);
});

test('every key results.mjs names exists, and each t() call fills exactly its placeholders', () => {
  const src = read(new URL('./results.mjs', import.meta.url));
  const calls = [...src.matchAll(/\bt\(\s*currentLang\s*,\s*'([^']+)'\s*(?:,\s*\{([^}]*)\})?/g)]
    .map(m => ({ key: m[1], names: m[2] ? [...m[2].matchAll(/(\w+)\s*:/g)].map(n => n[1]) : [] }));
  assert.ok(calls.length > 10, 'the t() scan found almost nothing; the pattern has drifted');
  const literals = [...src.matchAll(/'((?:results|nav|theme|lang)\.[\w.]+)'/g)].map(m => m[1]);
  assert.deepEqual([...new Set([...calls.map(c => c.key), ...literals])].filter(k => !has(k)), []);
  const problems = [];
  for (const { key, names } of calls) {
    for (const lang of LANGS) {
      const want = slots(STRINGS[lang][key] || '');
      for (const s of want) if (!names.includes(s)) problems.push(`${key} [${lang}] is never given {${s}}`);
      for (const g of names) if (!want.has(g)) problems.push(`${key} [${lang}] has no {${g}}`);
    }
  }
  assert.deepEqual(problems, []);
});

test('the nav reads simulation, agents, results (active), monitor, review', () => {
  const nav = read(HTML).match(/<nav[^>]*>([\s\S]*?)<\/nav>/);
  assert.ok(nav, 'results.html has no <nav>');
  const links = [...nav[1].matchAll(/<a\b([^>]*)>/g)].map(m => m[1]);
  const attr = (a, name) => (a.match(new RegExp(`${name}="([^"]+)"`)) || [])[1];
  assert.deepEqual(links.map(a => attr(a, 'href')), ['/simulation', '/agents', '/results', '/', '/review']);
  assert.deepEqual(links.map(a => attr(a, 'data-i18n')),
    ['nav.simulation', 'nav.agents', 'nav.results', 'nav.monitor', 'nav.review']);
  assert.deepEqual(links.map(a => /\bclass="[^"]*\bactive\b/.test(a)), [false, false, true, false, false]);
  assert.deepEqual(links.map(a => attr(a, 'aria-current') || null), [null, null, 'page', null, null]);
});

test('the page module and the markup carry no literal invisible character', () => {
  // An isolate in the markup is a character reference (&#x2066;), never the
  // character: an editor shows neither, and the Write tool decodes escapes.
  const banned = [0x2066, 0x2067, 0x2068, 0x2069, 0x200f, 0x200e, 0x202f, 0x2212, 0x2011];
  for (const url of [new URL('./results.mjs', import.meta.url), HTML]) {
    const found = [...read(url)].filter(c => banned.includes(c.codePointAt(0))).map(c => c.codePointAt(0).toString(16));
    assert.deepEqual(found, [], `${url.pathname} holds literal invisible characters`);
  }
});

test('results.html carries no figure of its own', () => {
  // verify_docs.py reads .html: the numbers live in the data, never in the
  // markup. The lab's footer (B58, the page index) is the only exception.
  const text = read(HTML)
    .replace(/<script[\s\S]*?<\/script>/g, '')
    .replace(/<footer[\s\S]*?<\/footer>/g, '')
    .replace(/<[^>]+>/g, ' ')
    .replace(/&#x[0-9a-f]+;/gi, '');
  assert.deepEqual(text.match(/\d+/g) || [], []);
});
