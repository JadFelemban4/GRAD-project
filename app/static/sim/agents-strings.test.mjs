// The /agents strings, and the three things the page borrows from the lab.
// node --test runs every test file in its own process, so the merge this file
// triggers never reaches panel.test.mjs or any other lab test.
import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { STRINGS, LANGS, missingKeys, t } from './i18n.mjs';

// Taken BEFORE agents-strings.mjs is imported: the lab's strings as the lab ships them.
const before = structuredClone(STRINGS);
let mod = null;
let loadError = null;
try { mod = await import('./agents-strings.mjs'); } catch (err) { loadError = err; }
const api = () => {
  assert.ok(mod, `agents-strings.mjs must load: ${loadError?.message}`);
  return mod;
};
// U+2011 NON-BREAKING HYPHEN, built from its code point so no editor can
// silently turn it back into an ASCII hyphen in this file.
const NB_HYPHEN = String.fromCodePoint(0x2011);

test('scene.mjs lends stage, ribbonGeometry and supra, and only adds the keyword', () => {
  // Design section 2, edit 2 (approved, section 11 Q2). Read as text so this
  // test needs no WebGL and no Three.js install.
  const src = readFileSync(new URL('./scene.mjs', import.meta.url), 'utf8');
  for (const name of ['stage', 'ribbonGeometry', 'supra']) {
    assert.match(src, new RegExp(`^export function ${name}\\(`, 'm'), `${name} is not exported`);
    assert.doesNotMatch(src, new RegExp(`^function ${name}\\(`, 'm'), `${name} is declared twice`);
  }
});

test('i18n.mjs carries nav.agents in both languages, right after nav.review', () => {
  assert.equal(before.ar['nav.agents'], 'الوكلاء');
  assert.equal(before.en['nav.agents'], 'Agents');
  for (const lang of LANGS) {
    const keys = Object.keys(before[lang]);
    assert.equal(keys.indexOf('nav.agents'), keys.indexOf('nav.review') + 1, `${lang}: nav.agents is not after nav.review`);
  }
});

test('the merge adds this page\'s strings and leaves every lab string as it was', () => {
  const { AGENT_STRINGS } = api();
  assert.deepEqual(Object.keys(AGENT_STRINGS).sort(), [...LANGS].sort());
  for (const lang of LANGS) {
    for (const [key, text] of Object.entries(before[lang])) assert.equal(STRINGS[lang][key], text, `${lang} ${key} changed`);
    for (const key of Object.keys(AGENT_STRINGS[lang])) {
      assert.ok(key.startsWith('agents.'), `${key} is not namespaced agents.`);
      assert.ok(!Object.prototype.hasOwnProperty.call(before[lang], key), `${key} already existed in the lab's ${lang}`);
      assert.equal(STRINGS[lang][key], AGENT_STRINGS[lang][key]);
    }
    assert.equal(Object.keys(STRINGS[lang]).length,
      Object.keys(before[lang]).length + Object.keys(AGENT_STRINGS[lang]).length);
  }
  assert.deepEqual(missingKeys(), []);
});

test('mergeStrings refuses a collision, a one-language key and an unknown language, and changes nothing', () => {
  const { mergeStrings } = api();
  const target = { ar: { a: 'أ' }, en: { a: 'A' } };
  const copy = structuredClone(target);
  assert.throws(() => mergeStrings(target, { ar: { a: 'ب', b: 'ب' }, en: { a: 'B', b: 'B' } }), /collides/);
  assert.deepEqual(target, copy);
  assert.throws(() => mergeStrings(target, { ar: { b: 'ب', c: 'ج' }, en: { b: 'B' } }), /missing from en/);
  assert.deepEqual(target, copy);
  assert.throws(() => mergeStrings(target, { ar: { b: 'ب' } }), /missing from en/);
  assert.throws(() => mergeStrings(target, { ar: { b: 'ب' }, en: { b: 'B' }, fr: { b: 'B' } }), /unknown language/);
  assert.deepEqual(target, copy);
  assert.equal(mergeStrings(target, { ar: { b: 'ب' }, en: { b: 'B' } }), 1);
  assert.deepEqual(target, { ar: { a: 'أ', b: 'ب' }, en: { a: 'A', b: 'B' } });
});

test('the honesty captions survive in both languages', () => {
  api();
  const mustSay = {
    'agents.badge': {
      ar: [/محاكاة/, /اصطناعي/, /أقسى من أي تسلّق مسجّل/, /لا يعني ذلك أنه أحرّ من كل لحظة/],
      en: [/simulation/i, /synthetic/, /harsher than any recorded climb/, /does not mean it is hotter than every moment/],
    },
    'agents.illustration': {
      ar: [/مثال توضيحي، لا نتيجة/, /وسيطات عبر 20 حلقة/, /لا يُحسب هنا أي فرق بين السيارتين/],
      en: [/illustration, not a result/, /medians over 20 episodes/, /no difference between the cars is computed/],
    },
    'agents.scene.slope': { ar: [/الميل غير مضخّم/, /ليست بمقياسها/], en: [/not exaggerated/, /not to scale/] },
    'agents.action.boost': { ar: [/سقف/], en: [/ceiling/] },
    'agents.action.map': { ar: [/السقف نفسه/, /لا يُعرض/], en: [/ceiling itself/, /not shown/] },
    'agents.action.tick_fan': { ar: [/المنمذَج/, /المروحة/, /0 أو 0\.4 أو 1\.0/], en: [/modelled/, /\bfan\b/, /0, 0\.4 or 1\.0/] },
    'agents.action.tick_pump': { ar: [/المنمذَج/, /المضخة/, /1\.0 ثابتة/], en: [/modelled/, /\bpump\b/, /constant 1\.0/] },
    'agents.action.held': { ar: [/حد سرعة التغيير/], en: [/rate limit/] },
    'agents.dt.caption': { ar: [/لم تُحلّ/, new RegExp(`H2${NB_HYPHEN}2`)], en: [/unresolved/, new RegExp(`H2${NB_HYPHEN}2`)] },
    'agents.turbine.reading': { ar: [/°م \/ .*°م$/], en: [/°C \/ .*°C$/] },
    'agents.damage.caption': { ar: [/في هذه الحلقة فقط/], en: [/in this episode only/] },
    'agents.legend.same_place': { ar: [/في المكان نفسه/], en: [/same place/] },
    'agents.device.line': { ar: [/لا تسجّل الجهاز/], en: [/do not record the device/] },
  };
  for (const [key, langs] of Object.entries(mustSay)) {
    for (const [lang, patterns] of Object.entries(langs)) {
      assert.ok(STRINGS[lang][key], `${key} missing in ${lang}`);
      for (const p of patterns) assert.match(STRINGS[lang][key], p, `${key} lost its caveat in ${lang}`);
    }
  }
  assert.match(t('ar', 'agents.profile.ve', { ve: 3 }), /×3/);
  assert.match(t('en', 'agents.profile.ve', { ve: 3 }), /×3/);
  assert.equal(STRINGS.ar['agents.footer.index'], '02 — AGENTS');
  assert.equal(STRINGS.en['agents.footer.index'], '02 — AGENTS');
});

test('no string says preview helps, and the engine computer is always the modelled one', () => {
  const { AGENT_STRINGS } = api();
  for (const lang of LANGS) {
    for (const [key, text] of Object.entries(AGENT_STRINGS[lang])) {
      assert.doesNotMatch(text, /preview helps/i, `${lang} ${key}`);
      assert.ok(!text.includes('يساعد الاستباق') && !text.includes('الاستباق يساعد'), `${lang} ${key}`);
      if (text.includes('حاسوب المحرك')) assert.ok(text.includes('المنمذَج'), `${key} names the engine computer without «المنمذَج»`);
    }
  }
});

// Rows 3 and 4 once shared one note that described the FAN's schedule. The
// modelled computer schedules only the fan (engine_env.py:265); the pump runs
// at thermal.py's default 1.0 throughout (engine_env.py:764-765). So each has
// its own note, and neither names the other device.
test('the fan and the pump each have their own note, and neither names the other', () => {
  const { AGENT_STRINGS } = api();
  for (const lang of LANGS) {
    assert.ok(!Object.prototype.hasOwnProperty.call(AGENT_STRINGS[lang], 'agents.action.tick_duty'),
      `${lang}: the shared duty note must be gone`);
  }
  assert.ok(!AGENT_STRINGS.ar['agents.action.tick_pump'].includes('المروحة'), 'the Arabic pump note names the fan');
  assert.ok(!AGENT_STRINGS.ar['agents.action.tick_fan'].includes('المضخة'), 'the Arabic fan note names the pump');
  assert.doesNotMatch(AGENT_STRINGS.en['agents.action.tick_pump'], /\bfan\b/, 'the English pump note names the fan');
  assert.doesNotMatch(AGENT_STRINGS.en['agents.action.tick_fan'], /\bpump\b/, 'the English fan note names the pump');
});

// At 1440 px in Arabic the caption broke as "H2-" | "2)": an ASCII hyphen is a
// line-break opportunity. U+2011 is not, and it must stay an escape in the
// source (agents-strings.mjs), never a literal character.
test('the dt caption\'s citation cannot break at its hyphen', () => {
  const { AGENT_STRINGS } = api();
  for (const lang of LANGS) {
    const text = AGENT_STRINGS[lang]['agents.dt.caption'];
    assert.ok(text.includes(`H2${NB_HYPHEN}2`), `${lang}: H2-2 must be written with U+2011`);
    assert.ok(!text.includes('H2-2'), `${lang}: an ASCII hyphen lets the line break inside H2-2`);
  }
  const src = readFileSync(new URL('./agents-strings.mjs', import.meta.url), 'utf8');
  assert.equal(src.split(NB_HYPHEN).length - 1, 0, 'a literal U+2011 in agents-strings.mjs: write the escape');
  assert.equal(src.split('H2\\u20112').length - 1, 2, 'the escape H2\\u20112 must appear once per language');
});

test('every key fills the same {placeholders} in both languages', () => {
  const { AGENT_STRINGS } = api();
  const slots = text => [...text.matchAll(/\{(\w+)\}/g)].map(m => m[1]).sort();
  for (const key of Object.keys(AGENT_STRINGS.ar)) {
    assert.deepEqual(slots(AGENT_STRINGS.ar[key]), slots(AGENT_STRINGS.en[key]), key);
  }
});

test('the bidi control characters in agents.pick.none and agents.device.line are pinned', () => {
  // \u2066 (LRI) / \u2069 (PDI) isolate the LTR address inside the Arabic
  // pick.none line, and \u200f (RLM) keeps the Arabic run after the {device}
  // placeholder in device.line reading right-to-left. All three are invisible in an
  // editor, so pin them here: a future edit that drops one silently would otherwise
  // not be caught until the string mis-renders.
  const { AGENT_STRINGS } = api();
  assert.ok(AGENT_STRINGS.ar['agents.pick.none'].includes('\u2066'), 'agents.pick.none lost its LRI');
  assert.ok(AGENT_STRINGS.ar['agents.pick.none'].includes('\u2069'), 'agents.pick.none lost its PDI');
  assert.ok(AGENT_STRINGS.ar['agents.device.line'].includes('\u200f'), 'agents.device.line lost its RLM');
});
