// The results tab's strings (results-strings.mjs), the merge that adds them to
// the lab's table, and the lab's one new key, nav.results (i18n.mjs).
// node --test runs every test file in its own process, so the merge this file
// triggers never reaches another test file.
//
// Characters that are invisible or look like ASCII (U+2066 / U+2068 / U+2069,
// the isolates; U+2212 MINUS SIGN; U+202F NARROW NO-BREAK SPACE) are built here
// from their code points, and an escape's TEXT from String.fromCharCode(92):
// the Write tool on this machine decodes a typed backslash-u escape into the
// character. One test checks that this file keeps to that rule.
import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { STRINGS, LANGS, missingKeys, t } from './i18n.mjs';

// Taken BEFORE results-strings.mjs is imported: the lab's strings as the lab ships them.
const before = structuredClone(STRINGS);
let mod = null;
let loadError = null;
try { mod = await import('./results-strings.mjs?v=R1a'); } catch (err) { loadError = err; }
const api = () => {
  assert.ok(mod, `results-strings.mjs must load: ${loadError?.message}`);
  return mod;
};

const cp = n => String.fromCodePoint(n);
const LRI = cp(0x2066);
const FSI = cp(0x2068);
const PDI = cp(0x2069);
const RLM = cp(0x200f);
const MINUS = cp(0x2212);
const NNBSP = cp(0x202f);
const escapeText = hex => `${String.fromCharCode(92)}u${hex}`;
const iso = text => `${LRI}${text}${PDI}`;
// Invisible, or easily taken for ASCII: never literal in a source file.
const INVISIBLE = [0x061c, 0x200b, 0x200e, 0x200f, 0x2011, 0x202a, 0x202b, 0x202c, 0x202d, 0x202e,
  0x202f, 0x2066, 0x2067, 0x2068, 0x2069, 0x2212, 0xfeff];
const ARABIC_LETTER = new RegExp(`[${cp(0x0621)}-${cp(0x064a)}]`);
const DIACRITICS = new RegExp(`[${cp(0x064b)}-${cp(0x0652)}${cp(0x0670)}]`, 'g');
const bare = text => text.normalize('NFC').replace(DIACRITICS, '');
const nfc = text => text.normalize('NFC');

// Contract section 5: every key, with its English exactly as the contract fixes it.
const CONTRACT = {
  'results.page.title': 'Results — GRAD',
  'results.intro.heading': 'Every experiment, as its files record it',
  'results.intro.note': 'Read from results/ every time this page opens. Nothing here is recomputed.',
  'results.footer.index': '03 — RESULTS',
  'results.loading': 'Reading the result files…',
  'results.error.fetch': 'Could not read the results ({status}).',
  'results.built.line': 'Read from commit {head} · Python {python} · plant {plant}',
  'results.built.git_unavailable': 'git is not available here, so the commit facts are left out.',
  'results.built.restart': 'The plant files changed after the server started: restart the server.',
  'results.built.derived_restart': 'The derived constants changed after the server started: restart the server.',
  'results.import_failure': 'Could not load {module} ({type}). Every section that needs it says so.',
  'results.summary.heading': 'Summary',
  'results.summary.note': 'Each row is a separate experiment, on its own plant and road; the rows are not to be counted together.',
  'results.summary.col.experiment': 'Experiment',
  'results.summary.col.plant': 'Plant',
  'results.summary.col.verdict': 'Verdict',
  'results.summary.no_verdict': 'No verdict recorded for this experiment',
  'results.summary.continues': "Continues {other}'s agents, on the same episodes",
  'results.section.no_name': '{prefix} (no name recorded)',
  'results.section.meta': '{episodes} frozen episodes · frozen {frozen} · protocol {protocol}',
  'results.section.unavailable.missing': 'Not available: {file} is missing. The command that makes it: {command}',
  'results.section.unavailable.read': 'Could not read {file}: {type}',
  'results.section.unavailable.module': 'Needs {module}, which could not be loaded.',
  'results.section.unavailable.build': 'Could not build this section: {type}',
  'results.plant.label': 'Plant',
  'results.plant.forced': 'Agents scored with a plant mismatch forced',
  'results.plant.not_recorded': 'Plant not recorded in this file',
  'results.plant.another': 'Made on another plant',
  'results.plant.cannot_compare': 'Cannot compare',
  'results.plant.same_code': 'Same plant code as this tree; derived constants not recorded',
  'results.plant.same': 'Same plant as this tree',
  'results.plant.mixed': 'The files of this experiment do not agree; per seed below',
  'results.plant.hashes': 'recorded {recorded} · this tree {live}',
  'results.plant.tag': 'the plant of {tag}',
  'results.plant.route_git': 'compared through git: recorded under another Python',
  'results.plant.reason.python': 'recorded under Python {recorded}; this server runs {live}, and git cannot reach the recorded commit',
  'results.plant.reason.no_git_route': "the recorded commit's plant files are not the ones that were hashed",
  'results.plant.reason.dirty': 'the plant files had uncommitted changes when it ran',
  'results.plant.reason.one_sided': 'a fingerprint field exists on one side only',
  'results.plant.reason.restart': 'the plant files changed after the server started; restart the server',
  'results.plant.reason.protocol': 'the protocol of this file is not known here',
  'results.plant.reason.import': 'the live fingerprint could not be built',
  'results.plant.reason.derived_differs': 'the derived constants differ',
  'results.plant.reason.derived_restart': 'the derived constants changed after the server started; restart the server',
  'results.plant.commits': 'from commits {list}',
  'results.plant.committed': 'last commit {commit} ({date})',
  'results.plant.changed': 'changed since its last commit ({date})',
  'results.plant.forced_lines': "The file's own lines:",
  'results.check.parse_equals_analysis.pass': "The medians read here equal analyse_phase_d.parse's.",
  'results.check.parse_equals_analysis.fail': "The medians read here differ from analyse_phase_d.parse's: {detail}",
  'results.check.parse_equals_analysis.not_compared': 'Not compared with analyse_phase_d.parse.',
  'results.verdict.heading': 'The preregistered verdict',
  'results.verdict.none': 'No verdict recorded for this experiment',
  'results.verdict.unavailable': 'The verdict could not be read here.',
  'results.verdict.lines': 'The text as written, with its file and line',
  'results.notes.heading': 'Not to be read without',
  'results.note.blind_not_blind': 'The blind agent was not fully blind: the climb came at the same second in every episode, so its thermal state could serve as a clock (results/PREREGISTRATION.md, limit 7).',
  'results.note.budget_c1': 'Trained for 50 000 steps, the C1 budget. The preregistration records it; these files do not.',
  'results.note.budget_from_file': "Trained for {steps} steps, as these files' model lines record.",
  'results.note.c4_not_converged': "The agents had not converged by C4's own rule, set on 23 September before any C4 agent trained (results/PREREGISTRATION_C4.md, 5b; results/C4_RESULT.txt).",
  'results.note.spark_bound_jad': 'Every agent pushes its spark trim to the +4° action bound (measured). The margin over current-grade with spark advance forbidden was measured for C4 on one episode, and not for Phase D or D2 (SESSION_REPORT_2026-09-30_merge.md).',
  'results.note.spike_unmeasured': "Every episode holds a one-step knock spike at the grade step; whether it moved this experiment's result was never measured (conflict.md).",
  'results.note.dt_mismatch': "Trained at a {train_dt} s step and scored at {eval_dt} s, as these files' note lines record.",
  'results.note.no_thermal_only': 'Damage without the knock term was not recorded in these files, so how much of each difference is the knock term is unknown.',
  'results.note.knock_model': 'The margin over current-grade rests on the knock model, which has not been tested on the car (drive C).',
  'results.note.turbine_modelled': "Turbine temperatures are modelled, not measured: no sensor on this car reads them, and the housing's heat capacity, c_turb, is assumed; it sets τ.",
  'results.note.no_other_notes': 'No other notes recorded for this experiment.',
  'results.chart.pairs.title': 'The pairs, seed by seed',
  'results.chart.pairs.what': "Each seed has two marks, the sighted agent and the blind one, joined by a line. The dashed line is current-grade's median.",
  'results.chart.pairs_thermal.title': 'The pairs, without the knock term',
  'results.chart.thermal_none': 'Damage without the knock term: not recorded in these files.',
  'results.chart.thermal_some': 'Without the knock term only for seeds {seeds}; the others did not record it.',
  'results.chart.hand.title': 'Against the hand-written policies',
  'results.chart.hand.what': "Each agent's median damage beside the three hand-written policies, from the same file.",
  'results.chart.axis.seed': 'Seed',
  'results.chart.axis.damage': 'Median damage over the frozen episodes (damage units)',
  'results.chart.axis.damage_thermal': 'Median damage without the knock term (damage units)',
  'results.chart.mei': 'The bracket is the minimum effect of interest, {mei} damage units.',
  'results.chart.mei_after': 'It was set on 22 September, after this result.',
  'results.chart.unavailable': 'This figure could not be drawn.',
  'results.chart.aria.pairs': 'The pairs of {name}',
  'results.chart.aria.hand': '{name} against the hand-written policies',
  'results.legend.sighted': 'Sighted agent',
  'results.legend.blind': 'Blind agent',
  'results.legend.baseline': 'Engine computer (modelled)',
  'results.legend.reactive': 'Reactive',
  'results.legend.current_grade': 'Current-grade',
  'results.tip.seed': 'Seed {seed}',
  'results.tip.median': 'median',
  'results.tip.worst': 'worst episode',
  'results.tip.fuel': 'median fuel (g)',
  'results.tip.peak': 'hottest turbine (°C, modelled)',
  'results.tip.diff': `blind ${MINUS} sighted`,
  'results.table.toggle': 'The numbers',
  'results.table.seed': 'Seed',
  'results.table.sighted': 'Sighted median',
  'results.table.blind': 'Blind median',
  'results.table.diff': `Blind ${MINUS} sighted`,
  'results.table.sighted_worst': 'Sighted worst',
  'results.table.blind_worst': 'Blind worst',
  'results.table.current_grade': 'Current-grade median',
  'results.table.baseline': 'Engine computer median',
  'results.table.reactive': 'Reactive median',
  'results.unpaired': 'Seed {seed} has no pair ({have}); it is not drawn.',
  'results.not_read.heading': 'Files not read',
  'results.not_read.reason.name': 'the name is not <prefix>_seed<N>.txt',
  'results.not_read.reason.header': 'the first line is not an evaluate.py header',
  'results.not_read.reason.no_fingerprint': 'no plant fingerprint block',
  'results.not_read.reason.no_table': 'no policy table',
  'results.not_read.reason.duplicate_role': 'more than one agent per arm',
  'results.not_read.reason.duplicate_seed': 'another file names the same seed',
  'results.not_read.reason.unreadable': 'could not be read ({type})',
  'results.markers.continues': 'continues',
};

// Every string this task adds, both languages: the tab's own and nav.results.
const added = lang => [...Object.entries(api().RESULTS_STRINGS[lang]), ['nav.results', STRINGS[lang]['nav.results']]];

test('i18n.mjs carries nav.results in both languages, right after nav.agents', () => {
  assert.equal(before.ar['nav.results'], 'النتائج');
  assert.equal(before.en['nav.results'], 'Results');
  for (const lang of LANGS) {
    const keys = Object.keys(before[lang]);
    assert.equal(keys.indexOf('nav.results'), keys.indexOf('nav.agents') + 1, `${lang}: nav.results is not right after nav.agents`);
    assert.equal(keys.indexOf('nav.agents'), keys.indexOf('nav.review') + 1, `${lang}: nav.agents moved from after nav.review`);
  }
});

test('every key of the contract is present, with the contract\'s English', () => {
  const { RESULTS_STRINGS } = api();
  for (const [key, en] of Object.entries(CONTRACT)) {
    assert.equal(RESULTS_STRINGS.en[key], en, `en ${key} is not the contract's text`);
    assert.equal(typeof RESULTS_STRINGS.ar[key], 'string', `ar ${key} is missing`);
  }
});

test('both languages carry the same keys, every one namespaced results.', () => {
  const { RESULTS_STRINGS } = api();
  assert.deepEqual(Object.keys(RESULTS_STRINGS).sort(), [...LANGS].sort());
  assert.deepEqual(Object.keys(RESULTS_STRINGS.ar).sort(), Object.keys(RESULTS_STRINGS.en).sort());
  for (const lang of LANGS) {
    for (const [key, text] of Object.entries(RESULTS_STRINGS[lang])) {
      assert.ok(key.startsWith('results.'), `${key} is not namespaced results.`);
      assert.equal(typeof text, 'string', `${lang} ${key}`);
      assert.ok(text.length > 0 && text === text.trim(), `${lang} ${key} is empty or padded`);
    }
  }
});

test('the merge adds the tab\'s strings and leaves every lab string as it was', () => {
  const { RESULTS_STRINGS } = api();
  for (const lang of LANGS) {
    for (const [key, text] of Object.entries(before[lang])) assert.equal(STRINGS[lang][key], text, `${lang} ${key} changed`);
    for (const key of Object.keys(RESULTS_STRINGS[lang])) {
      assert.ok(!Object.prototype.hasOwnProperty.call(before[lang], key), `${key} already existed in the lab's ${lang}`);
      assert.equal(STRINGS[lang][key], RESULTS_STRINGS[lang][key]);
    }
    assert.equal(Object.keys(STRINGS[lang]).length,
      Object.keys(before[lang]).length + Object.keys(RESULTS_STRINGS[lang]).length);
  }
  assert.deepEqual(missingKeys(), []);
});

test('mergeInto refuses a collision, a one-language key and an unknown language, and changes nothing', () => {
  const { mergeInto } = api();
  const target = { ar: { a: 'أ' }, en: { a: 'A' } };
  const copy = structuredClone(target);
  assert.throws(() => mergeInto(target, { ar: { a: 'ب', b: 'ب' }, en: { a: 'B', b: 'B' } }), /collides/);
  assert.deepEqual(target, copy);
  assert.throws(() => mergeInto(target, { ar: { b: 'ب', c: 'ج' }, en: { b: 'B' } }), /missing from en/);
  assert.deepEqual(target, copy);
  assert.throws(() => mergeInto(target, { ar: { b: 'ب' } }), /missing from en/);
  assert.deepEqual(target, copy);
  assert.throws(() => mergeInto(target, { ar: { b: 'ب' }, en: { b: 'B' }, fr: { b: 'B' } }), /unknown language/);
  assert.deepEqual(target, copy);
  assert.equal(mergeInto(target, { ar: { b: 'ب' }, en: { b: 'B' } }), 1);
  assert.deepEqual(target, { ar: { a: 'أ', b: 'ب' }, en: { a: 'A', b: 'B' } });
});

test('every key fills the same {placeholders} in both languages', () => {
  const { RESULTS_STRINGS } = api();
  const slots = text => [...text.matchAll(/\{(\w+)\}/g)].map(m => m[1]).sort();
  for (const key of Object.keys(RESULTS_STRINGS.en)) {
    assert.deepEqual(slots(RESULTS_STRINGS.ar[key]), slots(RESULTS_STRINGS.en[key]), key);
  }
});

// Spec 5.5 and contract section 0, in both languages: an English phrase is
// caught in an Arabic line too. The Arabic is compared without its vowel marks.
const FORBIDDEN_EN = [
  /preview\s+(?:helps|does\s+not\s+help|doesn't\s+help|did\s+not\s+help|cannot\s+help|is\s+useless)/i,
  /adds nothing measurable/i, /not from seeing ahead/i, /learning to protect/i, /replicat/i, /pooled/i,
];
const FORBIDDEN_AR = ['الاستباق يساعد', 'يساعد الاستباق', 'الاستباق لا يفيد', 'لا يفيد الاستباق',
  'الاستباق لا يساعد', 'المعاينة لا تفيد', 'المعاينة'];
test('no line says preview helps or does not help, nor any phrase the project retired', () => {
  for (const lang of LANGS) {
    for (const [key, text] of added(lang)) {
      for (const re of FORBIDDEN_EN) assert.doesNotMatch(text, re, `${lang} ${key}`);
      for (const phrase of FORBIDDEN_AR) assert.ok(!bare(text).includes(phrase), `${lang} ${key} says «${phrase}»`);
    }
  }
});

// current-grade and its Arabic name «الميل الحالي» are exempt; nothing else may
// call a file or a result current, stale, outdated, fresh or up to date.
const BANNED_EN = [/\bcurrent/i, /\bstale\b/i, /\boutdated\b/i, /\bfresh/i, /\bup[\s-]+to[\s-]+date\b/i];
const BANNED_AR = ['حديث', 'قديم', 'محدث', 'حالي'];
test('none of the banned words, in either language, current-grade exempt', () => {
  for (const lang of LANGS) {
    for (const [key, text] of added(lang)) {
      const en = text.replace(/current-grade/gi, '');
      for (const re of BANNED_EN) assert.doesNotMatch(en, re, `${lang} ${key}`);
      const ar = bare(text).replace(/الميل الحالي/g, '');
      for (const word of BANNED_AR) assert.ok(!ar.includes(word), `${lang} ${key} uses «${word}»`);
    }
  }
});

test('the engine computer is always «حاسوب المحرك المنمذَج», the modelled one', () => {
  const { RESULTS_STRINGS } = api();
  const NAME = 'حاسوب المحرك';
  const FULL = 'حاسوب المحرك المنمذَج';
  for (const [key, text] of Object.entries(RESULTS_STRINGS.ar)) {
    assert.equal(text.split(NAME).length, text.split(FULL).length, `ar ${key} names the engine computer without «المنمذَج»`);
    assert.ok(!text.includes('ECU') && !text.includes('وحدة التحكم'), `ar ${key} names the engine computer another way`);
  }
  assert.equal(RESULTS_STRINGS.ar['results.legend.baseline'], FULL);
  assert.ok(RESULTS_STRINGS.ar['results.table.baseline'].includes(FULL));
  assert.match(RESULTS_STRINGS.en['results.legend.baseline'], /\(modelled\)/);
});

test('current-grade stays Latin in Arabic, inside a left-to-right isolate', () => {
  const { RESULTS_STRINGS } = api();
  for (const [key, en] of Object.entries(RESULTS_STRINGS.en)) {
    if (/current-grade/i.test(en)) {
      assert.ok(RESULTS_STRINGS.ar[key].includes(iso('current-grade')), `ar ${key}: current-grade is not isolated`);
    }
  }
  assert.equal(RESULTS_STRINGS.ar['results.legend.current_grade'], `سياسة ${iso('current-grade')}`);
});

test('the knock is «الطَّرْق» with its marks, so it cannot be read as «الطرق», the roads', () => {
  const { RESULTS_STRINGS } = api();
  const forms = ['الطَّرْق', 'طَرْق'].map(nfc);
  for (const [key, en] of Object.entries(RESULTS_STRINGS.en)) {
    const ar = RESULTS_STRINGS.ar[key];
    assert.ok(!ar.includes('طرق'), `ar ${key}: an unmarked «طرق» reads as roads`);
    if (/knock/i.test(en)) assert.ok(forms.some(f => nfc(ar).includes(f)), `ar ${key} does not name the knock`);
  }
});

// The two lines that stay Latin in both languages, outside any isolate: the
// window title (as the lab's and /agents' titles are) and the footer index,
// which sits in a dir="ltr" span.
const LATIN_OK = new Set(['results.page.title', 'results.footer.index']);
const ISOLATE_RUN = new RegExp(`${LRI}[^${LRI}${FSI}${PDI}]*${PDI}`, 'g');
test('in Arabic every Latin letter and digit sits inside an isolate; English lines carry none', () => {
  const { RESULTS_STRINGS } = api();
  for (const [key, text] of Object.entries(RESULTS_STRINGS.ar)) {
    const outside = text.replace(ISOLATE_RUN, '');
    for (const c of [LRI, FSI, PDI]) assert.ok(!outside.includes(c), `ar ${key}: an isolate is not closed, or is nested`);
    if (LATIN_OK.has(key)) continue;
    assert.doesNotMatch(outside.replace(/\{\w+\}/g, ''), /[A-Za-z0-9]/, `ar ${key}: Latin or a digit outside an isolate`);
    assert.match(text, ARABIC_LETTER, `ar ${key} has no Arabic letter: is it translated?`);
  }
  for (const [key, text] of Object.entries(RESULTS_STRINGS.en)) {
    for (const c of [LRI, FSI, PDI, RLM]) assert.ok(!text.includes(c), `en ${key}: an English line needs no isolate`);
  }
});

// A slot that always holds ONE number, hash, commit, date, path, module or
// protocol is isolated by the Arabic line itself, so it keeps its order
// whatever the caller passes. A slot that may hold Arabic words or a list
// stays bare, and the caller isolates each Latin item in it (contract 4.5).
const ISOLATED_SLOTS = new Set(['command', 'commit', 'date', 'detail', 'episodes', 'eval_dt', 'file', 'frozen',
  'head', 'live', 'mei', 'module', 'plant', 'prefix', 'protocol', 'python', 'recorded', 'seed', 'status',
  'steps', 'tag', 'train_dt', 'type']);
const BARE_SLOTS = new Set(['have', 'list', 'name', 'other', 'seeds']);
const slotDepths = text => {
  const out = [];
  let depth = 0;
  for (let i = 0; i < text.length; i += 1) {
    const c = text[i];
    if (c === LRI || c === FSI) depth += 1;
    else if (c === PDI) depth -= 1;
    else if (c === '{') {
      const m = /^\{(\w+)\}/.exec(text.slice(i));
      if (m) out.push({ slot: m[1], isolated: depth > 0 });
    }
  }
  return out;
};
test('in Arabic a slot holding one number, hash or path is isolated; a list or a name is not', () => {
  const { RESULTS_STRINGS } = api();
  for (const [key, text] of Object.entries(RESULTS_STRINGS.ar)) {
    for (const { slot, isolated } of slotDepths(text)) {
      assert.ok(ISOLATED_SLOTS.has(slot) || BARE_SLOTS.has(slot), `ar ${key}: {${slot}} is in neither list; classify it`);
      assert.equal(isolated, ISOLATED_SLOTS.has(slot), `ar ${key}: {${slot}} ${isolated ? 'must not be' : 'must be'} isolated`);
    }
  }
});

test('the notes keep their clauses in Arabic, and their literal numbers are isolated', () => {
  const { RESULTS_STRINGS } = api();
  const AR = RESULTS_STRINGS.ar;
  const mustSay = {
    'results.note.blind_not_blind': ['لم يكن الوكيل الأعمى أعمى تماماً', 'الثانية نفسها في كل حلقة', 'كساعة', iso('results/PREREGISTRATION.md'), iso('7')],
    'results.note.budget_c1': [iso(`50${NNBSP}000`), iso('C1'), 'التسجيل المسبق', 'لا تذكرها هذه الملفات'],
    'results.note.budget_from_file': [iso('{steps}'), 'أسطر النموذج'],
    'results.note.c4_not_converged': ['لم يستقر تدريب الوكلاء', iso('C4'), iso('23'), iso('results/PREREGISTRATION_C4.md'), iso('results/C4_RESULT.txt')],
    'results.note.spark_bound_jad': [iso('+4°'), 'تعديل توقيت الشرارة', 'منع تبكير الشرارة', iso('C4'), 'على حلقة واحدة',
      'ولم يُقَس', iso('Phase D'), iso('D2'), iso('SESSION_REPORT_2026-09-30_merge.md')],
    'results.note.spike_unmeasured': ['قفزة طَرْق', 'خطوة واحدة', 'لم يُقَس قطّ', iso('conflict.md')],
    'results.note.dt_mismatch': [iso('{train_dt}'), iso('{eval_dt}'), 'أسطر الملاحظات'],
    'results.note.no_thermal_only': ['لم تسجّل هذه الملفات', 'لا يُعرف'],
    'results.note.knock_model': [iso('current-grade'), 'نموذج الطَّرْق', 'لم يُختبر على السيارة', iso('C')],
    'results.note.turbine_modelled': ['منمذَجة لا مقيسة', 'لا حساس', iso('c_turb'), 'مفترَضة', iso('τ')],
    'results.summary.note': ['تجربة مستقلة', 'لا تُدمج الصفوف في نتيجة واحدة'],
    'results.intro.note': [iso('results/'), 'لا يُعاد هنا حساب أي شيء'],
    'results.chart.mei': [iso('{mei}'), 'الحد الأدنى المهم', 'وحدة ضرر'],
    'results.chart.mei_after': [iso('22'), 'بعد هذه النتيجة'],
    'results.plant.same_code': ['الثوابت المشتقة غير'],
    'results.tip.peak': ['منمذَجة'],
  };
  for (const [key, phrases] of Object.entries(mustSay)) {
    for (const phrase of phrases) assert.ok(nfc(AR[key]).includes(nfc(phrase)), `ar ${key} lost «${phrase}»`);
  }
  for (const lang of LANGS) {
    for (const key of ['results.tip.diff', 'results.table.diff']) {
      assert.ok(RESULTS_STRINGS[lang][key].includes(MINUS), `${lang} ${key}: subtract with U+2212`);
      assert.ok(!RESULTS_STRINGS[lang][key].includes(' - '), `${lang} ${key}: an ASCII hyphen is not a minus sign`);
    }
  }
});

test('the footer index is the same in both languages, and the title follows the lab\'s pattern', () => {
  const { RESULTS_STRINGS } = api();
  assert.equal(RESULTS_STRINGS.ar['results.footer.index'], '03 — RESULTS');
  assert.equal(RESULTS_STRINGS.en['results.footer.index'], RESULTS_STRINGS.ar['results.footer.index']);
  assert.equal(RESULTS_STRINGS.ar['results.page.title'], 'النتائج — GRAD');
});

test('t() fills a results line in both languages, leaving no placeholder', () => {
  api();
  for (const lang of LANGS) {
    const line = t(lang, 'results.built.line', { head: 'abc1234', python: '3.12.10', plant: 'f00dbabe' });
    for (const value of ['abc1234', '3.12.10', 'f00dbabe']) assert.ok(line.includes(value), `${lang}: ${line}`);
    assert.doesNotMatch(line, /\{\w+\}/, `${lang}: an unfilled placeholder in ${line}`);
  }
  assert.equal(t('en', 'results.unpaired', { seed: 3, have: 'sighted' }), 'Seed 3 has no pair (sighted); it is not drawn.');
  assert.equal(t('ar', 'results.tip.seed', { seed: 3 }), `بذرة ${iso('3')}`);
});

test('results-strings.mjs carries its invisible characters as escapes, never literally', () => {
  const src = readFileSync(new URL('./results-strings.mjs', import.meta.url), 'utf8');
  for (const code of INVISIBLE) {
    assert.equal(src.split(cp(code)).length - 1, 0, `a literal U+${code.toString(16)} in results-strings.mjs: write the escape`);
  }
  const count = hex => src.split(escapeText(hex)).length - 1;
  assert.ok(count('2066') > 0, 'the Arabic lines isolate their Latin runs');
  assert.equal(count('2066'), count('2069'), 'every isolate opened in the source is closed');
  assert.equal(count('2212'), 4, 'U+2212: blind minus sighted, in the tooltip and the table, in both languages');
  assert.equal(count('202f'), 1, 'U+202F: the Arabic 50 000 of results.note.budget_c1');
  assert.match(src, /^import \{ STRINGS \} from '\.\/i18n\.mjs';$/m, 'the lab table comes from i18n.mjs, unversioned');
});

test('this file builds its characters from code points, never from a typed escape', () => {
  const own = readFileSync(new URL(import.meta.url), 'utf8');
  for (const code of INVISIBLE) assert.equal(own.split(cp(code)).length - 1, 0, `a literal U+${code.toString(16)} in this test file`);
  assert.equal(own.split(escapeText('')).length - 1, 0, 'a typed backslash-u escape in this test file');
});

// The tab imports results-strings.mjs with ONE version query everywhere
// (contract section 4), so the browser keeps one copy. A second copy (another
// query, or none) must fail loudly, and must not touch the table. The second
// address is built at run time, so no import in this file's text carries a
// query other than the tab's own.
test('a second copy of the module refuses to merge again, and changes nothing', async () => {
  api();
  const snapshot = structuredClone(STRINGS);
  const second = new URL('./results-strings.mjs', import.meta.url);
  second.searchParams.set('v', 'second-copy');
  await assert.rejects(import(second.href), /collides/);
  assert.deepEqual(STRINGS, snapshot);
});
