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

// U+2066 / U+2069 isolate a left-to-right run, U+200F is a right-to-left mark,
// U+2212 is the minus sign and U+202F the narrow no-break space. Each is
// invisible or looks like an ASCII character in an editor, so this file builds
// them from their code points, and the source of agents-strings.mjs must carry
// them as escapes, never as literal characters.
const LRI = String.fromCodePoint(0x2066);
const PDI = String.fromCodePoint(0x2069);
const RLM = String.fromCodePoint(0x200f);
const MINUS = String.fromCodePoint(0x2212);
const escapeText = hex => `${String.fromCharCode(92)}u${hex}`;

test('the bidi control characters are pinned', () => {
  // M2: the picker works from the nav link, so agents.pick.none names no
  // address and carries no isolate any more. device.line keeps its RLM, which
  // keeps the Arabic run after the {device} placeholder reading right-to-left.
  const { AGENT_STRINGS } = api();
  for (const lang of LANGS) {
    const none = AGENT_STRINGS[lang]['agents.pick.none'];
    assert.ok(!none.includes(LRI) && !none.includes(PDI), `${lang}: agents.pick.none still isolates an address`);
    assert.ok(!none.includes('?runs='), `${lang}: agents.pick.none still tells the viewer to type an address`);
  }
  assert.ok(AGENT_STRINGS.ar['agents.device.line'].includes(RLM), 'agents.device.line lost its RLM');
});

test('the pair row\'s minus is U+2212, written as an escape', () => {
  const { AGENT_STRINGS } = api();
  for (const lang of LANGS) {
    const row = AGENT_STRINGS[lang]['agents.pick.pair_row'];
    assert.ok(row, `${lang}: agents.pick.pair_row is missing`);
    assert.ok(row.includes(MINUS), `${lang}: the pair row must subtract with U+2212`);
    assert.ok(!row.includes(' - '), `${lang}: an ASCII hyphen is not a minus sign`);
  }
  const src = readFileSync(new URL('./agents-strings.mjs', import.meta.url), 'utf8');
  assert.equal(src.split(escapeText('2212')).length - 1, 2, 'the U+2212 escape must appear once per language');
  for (const hex of ['2066', '2069', '200f', '2011', '2212', '202f']) {
    assert.equal(src.split(String.fromCodePoint(parseInt(hex, 16))).length - 1, 0,
      `a literal U+${hex} in agents-strings.mjs: write the escape`);
  }
});

// A name the server made up ends in a parenthesis: 'runs_sixspeed_18sep (no
// name recorded)'. In an Arabic line the closing parenthesis sits between the
// Latin name and Arabic text, so it takes the line's right-to-left direction
// and is drawn mirrored (UAX #9 N1/N2), unless {name} is its own first-strong
// isolate, U+2068 ... U+2069. Written as escapes in agents-strings.mjs.
const FSI = String.fromCodePoint(0x2068);
test('a name in the Arabic refused labels is isolated, so its parenthesis is not mirrored', () => {
  const { AGENT_STRINGS } = api();
  for (const key of ['agents.pick.refused_pair', 'agents.pick.experiment_refused']) {
    assert.ok(AGENT_STRINGS.ar[key].includes(`${FSI}{name}${PDI}`), `ar ${key}: {name} is not inside U+2068 ... U+2069`);
  }
  const src = readFileSync(new URL('./agents-strings.mjs', import.meta.url), 'utf8');
  assert.equal(src.split(escapeText('2068')).length - 1, 2, 'the U+2068 escape must appear once per refused label');
  assert.equal(src.split(FSI).length - 1, 0, 'a literal U+2068 in agents-strings.mjs: write the escape');
});

test('the M2 picker strings keep their clauses', () => {
  const { AGENT_STRINGS } = api();
  const mustSay = {
    'agents.pick.none': { ar: [/لم يُختر شيء/, /اختر تجربة/, /احسب/], en: [/Nothing is selected/, /choose an experiment/, /Compute/] },
    'agents.pick.pair_qualifier': {
      ar: [/فرق وسيطَي 20 حلقة/, /طريقها وأوزانها/, /ليست هذه الحلقة/],
      en: [/medians of 20 episodes/, /own road and weights/, /not this episode/],
    },
    'agents.pick.pair_qualifier_same_road': {
      ar: [/فرق وسيطَي 20 حلقة/, /الطريق نفسه/, /ليست هذه الحلقة/],
      en: [/medians of 20 episodes/, /same road/, /not this episode/],
    },
    'agents.pick.episode_option_same_road': { ar: [/الطريق نفسه/, /الأوزان/], en: [/same road/, /weights/] },
    'agents.pick.same_road_note': { ar: [/الطريق نفسه/, /في الأوزان فقط/], en: [/same road/, /only in their weights/] },
    'agents.pick.pair_refused': { ar: [/لا يمكن تشغيله/], en: [/cannot run/] },
    'agents.pick.experiment_refused': { ar: [/لا يمكن تشغيل أي زوج/], en: [/no pair can run/] },
    'agents.car.blind_phase_d': {
      ar: [/^لا يرى الطريق أمامه/, /قد يحفظه/, /الطريق نفسه في كل حلقة/],
      en: [/^Does not see the road ahead/, /memorised/, /same road in every episode/],
    },
    'agents.seen.blind_phase_d': { ar: [/^لا يرى الطريق أمامه/, /قد يحفظه/], en: [/^Does not see the road ahead/, /memorised/] },
    'agents.load.stopping': { ar: [/يُوقَف/, /السابقة/], en: [/Stopping/, /previous/] },
    // The catalog's third 'scored' value (Task 3): results/ records a different
    // zip sha, so this is not the artefact that was scored and the pair is refused.
    'agents.verdict.scored_mismatch': {
      ar: [/ليس هذا هو الملف الذي قُيِّم/, /تختلف/, /لا يمكن تشغيل هذا الزوج/],
      en: [/Not the scored artefact/, /differs/, /cannot run/],
    },
  };
  for (const [key, langs] of Object.entries(mustSay)) {
    for (const [lang, patterns] of Object.entries(langs)) {
      assert.ok(AGENT_STRINGS[lang][key], `${key} missing in ${lang}`);
      for (const p of patterns) assert.match(AGENT_STRINGS[lang][key], p, `${key} lost a clause in ${lang}`);
    }
  }
  assert.notEqual(AGENT_STRINGS.ar['agents.pick.pair_qualifier'], AGENT_STRINGS.ar['agents.pick.pair_qualifier_same_road']);
  for (const lang of LANGS) {
    const seen = t(lang, 'agents.seen.blind_phase_d', { zeros: '0 · 0 · 0 · 0', cite: 'results/PHASE_D_RESULT.txt:33-40' });
    assert.ok(seen.includes('0 · 0 · 0 · 0') && seen.includes('results/PHASE_D_RESULT.txt:33-40'), `${lang}: ${seen}`);
    assert.doesNotMatch(seen, /[{][a-z0-9_]+[}]/i, `${lang}: an unfilled placeholder in ${seen}`);
  }
});

// M3: the models panel (model-panel.mjs), behind the footer gesture. The
// Arabic honesty lines are design 7.7, 7.5b and 7.8 of
// docs/superpowers/specs/2026-09-28-agent-replay-m3-design.md, word for word,
// so they are pinned whole; the rest keep the clauses that carry a caveat.
const M3_KEYS = [
  'agents.pause.empty',
  'agents.models.heading', 'agents.models.not_thesis', 'agents.models.claim', 'agents.models.levels',
  'agents.models.jev.name', 'agents.models.jev.where', 'agents.models.jev.text',
  'agents.models.jev.status.configured', 'agents.models.jev.status.no_key',
  'agents.models.jev.ask', 'agents.models.jev.latency',
  'agents.models.laya.name', 'agents.models.laya.where', 'agents.models.laya.device_unknown',
  'agents.models.laya.text', 'agents.models.laya.check',
  'agents.models.laya.status.not_configured', 'agents.models.laya.status.not_found',
  'agents.models.laya.status.stopped', 'agents.models.laya.status.starting',
  'agents.models.laya.status.ready', 'agents.models.laya.status.failed',
  'agents.models.laya.ask', 'agents.models.laya.latency', 'agents.models.laya.first_load',
  'agents.models.reason.pause', 'agents.models.reason.not_done', 'agents.models.reason.stopped',
  'agents.models.reason.asking',
  'agents.models.ask_this', 'agents.models.reference', 'agents.models.choice', 'agents.models.chosen_p',
  'agents.models.reversed', 'agents.models.held', 'agents.models.changed',
  'agents.models.footer', 'agents.models.sent', 'agents.models.no_answer', 'agents.models.no_answer_plain',
  'agents.models.error.server_error',
];

test('the M3 strings keep their clauses', () => {
  const { AGENT_STRINGS } = api();
  for (const lang of LANGS) {
    const missing = M3_KEYS.filter(key => !Object.prototype.hasOwnProperty.call(AGENT_STRINGS[lang], key));
    assert.deepEqual(missing, [], `${lang}: M3 keys missing`);
  }
  const verbatim = {
    'agents.models.not_thesis': 'ليس جزءاً من الرسالة ولا من أي نتيجة. لا يقارن أي رقم هنا النموذجين بالوكيلين، ولا يُحسب أي فرق.',
    'agents.models.claim': 'الاحتمالات ادعاء النموذج نفسه، ولم تُختبر على هذه المهمة.',
    'agents.models.levels': 'كل نموذج يختار واحداً من خمسة مستويات لكل إجراء: للتعديلات الثلاثة الحدّان و"بلا تعديل" ونقطتان في المنتصف؛ وللمروحة والمضخة خمس قيم متساوية التباعد. المعروض هو اختيار النموذج نفسه، ولا يُحسب منه متوسط.',
    'agents.models.laya.check': 'نسأل لايا مرتين، والخيارات بترتيبين متعاكسين. إذا تغيّر اختياره بتغيير الترتيب وحده، فذلك الاختيار لا يأتي من حالة المحرك.',
    'agents.models.held': 'ثبت',
    'agents.models.changed': 'تغيّر بتغيير الترتيب',
    'agents.pause.empty': 'اضغط احسب، ثم أوقف العرض عند أي ثانية لترى ما قرّره كل وكيل',
  };
  for (const [key, text] of Object.entries(verbatim)) assert.equal(AGENT_STRINGS.ar[key], text, `ar ${key} is not the design's line`);
  const mustSay = {
    'agents.models.not_thesis': { en: [/not part of the thesis/i, /no difference is computed/] },
    'agents.models.claim': { en: [/model's own claim/, /untested/] },
    'agents.models.levels': { en: [/five levels/, /no average is computed/] },
    'agents.models.laya.check': { en: [/twice/, /opposite orders/, /does not come from the engine state/] },
    'agents.models.laya.text': {
      ar: [/لا يُرسل شيئاً خارجه/, /تجربة تشغيل، لا تقييم/, /README_AR\.md:31/],
      en: [/sends nothing out of it/, /A trial run, not an evaluation/, /README_AR\.md:31/],
    },
    'agents.models.jev.text': {
      ar: [/الولايات المتحدة/, /بلا حدّ زمني \(MCA §4\.1\)/, /تمنع تدريب/, /غير معروف/, /الدقة العددية/],
      en: [/USA/, /in perpetuity/, /\(MCA §4\.1\)/, /forbids training/, /unknown/, /numeric precision/],
    },
    'agents.models.jev.where': { ar: [/الولايات المتحدة/, /مدفوع/], en: [/USA/, /paid/] },
    'agents.models.jev.ask': { ar: [/مدفوع/], en: [/paid/] },
    'agents.models.jev.latency': { ar: [/مقيسة من هذا الجهاز/, /70–500 ms/], en: [/measured from this machine/, /70–500 ms/] },
    'agents.models.laya.where': { ar: [/على هذا الجهاز/], en: [/On this machine/] },
    'agents.models.footer': { ar: [/لم يُطبَّق/, /حد سرعة التغيير/], en: [/not applied/, /not rate-limited/] },
    'agents.models.error.vendor_status': { ar: [/HTTP \{status\}/, /رصيد/], en: [/HTTP \{status\}/, /credit/] },
    'agents.models.error.no_key': { ar: [/لم يُرسل شيء/], en: [/nothing was sent/] },
    'agents.pause.empty': { en: [/Compute/, /pause/] },
  };
  for (const [key, langs] of Object.entries(mustSay)) {
    for (const [lang, patterns] of Object.entries(langs)) {
      assert.ok(AGENT_STRINGS[lang][key], `${key} missing in ${lang}`);
      for (const p of patterns) assert.match(AGENT_STRINGS[lang][key], p, `${key} lost a clause in ${lang}`);
    }
  }
  // Design 7.7: the reference line names no car on its own and subtracts
  // nothing; the page puts the two lane values after its colon.
  for (const lang of LANGS) {
    const ref = AGENT_STRINGS[lang]['agents.models.reference'];
    assert.ok(ref.endsWith(':'), `${lang}: the reference line ends at its colon`);
    assert.doesNotMatch(ref, /[{][a-z0-9_]+[}]/i, `${lang}: the reference line takes no placeholder`);
  }
  // Design C9: the page never shows the model's confidence.
  for (const lang of LANGS) {
    for (const key of Object.keys(AGENT_STRINGS[lang]).filter(k => k.startsWith('agents.models.'))) {
      assert.doesNotMatch(AGENT_STRINGS[lang][key], /confidence|الثقة/i, `${lang} ${key} names the confidence`);
    }
  }
});
