// results-view.mjs, without a browser: which string each line of a section
// uses, which values go into it, and that every value inside an Arabic
// sentence sits in a left-to-right isolate. English is asserted as the
// contract writes it; Arabic through t() with the isolated values, so these
// tests check the choice and the isolation, not the Arabic wording (which
// results-strings.test.mjs owns).
import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { t } from './i18n.mjs';
import './results-strings.mjs?v=R1a';
import {
  sectionName, nameSlot, metaText, plantView, verdictView, noteItems, summaryRows, unavailableText,
  notReadItems, builtView, checkItems, unpairedItems, thermalNote, meiLines,
} from './results-view.mjs?v=R1a';

const LRI = String.fromCodePoint(0x2066);
const PDI = String.fromCodePoint(0x2069);
const NNBSP = String.fromCodePoint(0x202f);
const MINUS = String.fromCodePoint(0x2212);
const EM_DASH = String.fromCodePoint(0x2014);
const iso = s => `${LRI}${s}${PDI}`;

// One file's classify_eval answer, as contract 2.2 shapes it.
function file(seed, over = {}) {
  return {
    state: 'another', reason: null, route: 'same_python', protocol: 'd2',
    recorded: { plant_sha: 'b5a3069f32a83754', python: '3.12.10', git_head: 'c5a5341548040f69', derived_sha: null },
    live: { plant_sha: 'c236a8db3e201090', python: '3.12.10' },
    differs: ['plant_sha'], tag: 'sep17-before-merge', forced: [],
    file: { rel: `results/c4_seed${seed}.txt`, commit: { short: 'a3a048e', date: '2026-09-22T03:02:51+03:00' }, changed: false },
    ...over,
  };
}
const PROV = {
  state: 'another', reason: null, tag: 'sep17-before-merge', commits: ['c5a5341'],
  files: { 0: file(0), 1: file(1) },
};
const VERDICT = {
  state: 'found',
  lines: [
    { key: 'result', file: 'C4_RESULT.txt', line: 40, text: '  RESULT: SMALLER THAN THE MEI' },
    { key: 'seeds', file: 'C4_RESULT.txt', line: 30, text: 'a\nb\nc' },
  ],
  missing: [],
  short: { ar: 'نص قصير', en: 'smaller than the MEI (50) at 300 000 steps' },
  cells: [{ cell: 'SMALLER THAN THE MEI', gloss: { ar: 'شرح', en: 'Preview effect below the threshold' } }],
};
function section(prefix, over = {}) {
  return {
    id: `exp-${prefix}`, kind: 'evaluation', state: 'ok', prefix, name: { phase_d: 'Phase D', d2: 'Phase D2', c4: 'C4' }[prefix] ?? null,
    known: true, order: 0, continues: null, protocol: 'd2', episodes: 20, frozen: '22 Sep 2026', scenario: 'climb',
    seeds: [], unpaired: [], mei: 50, mei_after_result: false, thermal_recorded: 'none',
    verdict: VERDICT, notes: [], provenance: PROV, checks: [], error: null, ...over,
  };
}

test('a section is named by run_phase_d, or by its prefix said to have no name; a name slot isolates only Latin', () => {
  assert.equal(sectionName(section('c4'), 'en'), 'C4');
  assert.equal(sectionName(section('zz', { name: null }), 'en'), 'zz (no name recorded)');
  assert.equal(sectionName(section('zz', { name: null }), 'ar'), t('ar', 'results.section.no_name', { prefix: iso('zz') }));
  // For a bare {name} slot: a recorded (Latin) name isolated, the no-name line as it is.
  assert.equal(nameSlot(section('c4'), 'ar'), iso('C4'));
  assert.equal(nameSlot(section('c4'), 'en'), 'C4');
  assert.equal(nameSlot(section('zz', { name: null }), 'ar'), sectionName(section('zz', { name: null }), 'ar'));
});

test('the meta line carries the header facts, isolated in Arabic', () => {
  assert.equal(metaText(section('c4'), 'en'), '20 frozen episodes · frozen 22 Sep 2026 · protocol d2');
  assert.equal(metaText(section('c4'), 'ar'),
    t('ar', 'results.section.meta', { episodes: iso('20'), frozen: iso('22 Sep 2026'), protocol: iso('d2') }));
  assert.equal(metaText(section('phase_d', { protocol: null }), 'en'), `20 frozen episodes · frozen 22 Sep 2026 · protocol ${EM_DASH}`);
});

test('a common plant state lists both hashes, the tag, the commits and each file commit once', () => {
  const v = plantView(PROV, 'en');
  assert.equal(v.state, 'another');
  assert.equal(v.text, 'Made on another plant');
  assert.deepEqual(v.details, [
    'recorded b5a3069f32a83754 · this tree c236a8db3e201090',
    'the plant of sep17-before-merge',
    'from commits c5a5341',
    'last commit a3a048e (2026-09-22T03:02:51+03:00)',
  ]);
  const ar = plantView(PROV, 'ar');
  assert.equal(ar.text, t('ar', 'results.plant.another'));
  assert.equal(ar.details[0], t('ar', 'results.plant.hashes', { recorded: iso('b5a3069f32a83754'), live: iso('c236a8db3e201090') }));
  assert.equal(ar.details[3], t('ar', 'results.plant.committed', { commit: iso('a3a048e'), date: iso('2026-09-22T03:02:51+03:00') }));
});

test('every state has its own label, and an unknown one claims nothing', () => {
  const want = {
    forced: 'Agents scored with a plant mismatch forced', not_recorded: 'Plant not recorded in this file',
    another: 'Made on another plant', cannot_compare: 'Cannot compare',
    same_code: 'Same plant code as this tree; derived constants not recorded', same: 'Same plant as this tree',
    mixed: 'The files of this experiment do not agree; per seed below', invented: 'Cannot compare',
  };
  for (const [state, text] of Object.entries(want)) {
    assert.equal(plantView({ ...PROV, state, files: {} }, 'en').text, text, state);
  }
});

test('a mixed section is told seed by seed, with each reason and each file\'s own facts', () => {
  // Spec 5.2: the facts appear in every state, mixed included. Seed 2's file is
  // modified (its last commit is not a fact about it) and reached through git;
  // seed 3's was forced (its own lines quoted, no hashes).
  const forced = '!! runs_c4/blind_seed3: PLANT MISMATCH';
  const prov = { state: 'mixed', reason: null, tag: null, commits: ['c5a5341'],
    files: {
      3: file(3, { state: 'forced', forced: [forced], tag: null, route: null }),
      1: file(1, { state: 'cannot_compare', reason: 'python', tag: null, route: null,
        recorded: { ...file(1).recorded, python: '3.13.2' } }),
      2: file(2, { state: 'same_code', tag: null, route: 'git', differs: [],
        recorded: { ...file(2).recorded, plant_sha: '9f1c2e3d4b5a6978', python: '3.13.2' },
        file: { rel: 'results/c4_seed2.txt', commit: { short: 'a3a048e', date: '2026-09-22T03:02:51+03:00' }, changed: true } }),
      0: file(0),
    } };
  assert.deepEqual(plantView(prov, 'en').details, [
    'Seed 0 · Made on another plant',
    'recorded b5a3069f32a83754 · this tree c236a8db3e201090',
    'the plant of sep17-before-merge',
    'last commit a3a048e (2026-09-22T03:02:51+03:00)',
    'Seed 1 · Cannot compare · recorded under Python 3.13.2; this server runs 3.12.10, and git cannot reach the recorded commit',
    'recorded b5a3069f32a83754 · this tree c236a8db3e201090',
    'last commit a3a048e (2026-09-22T03:02:51+03:00)',
    'Seed 2 · Same plant code as this tree; derived constants not recorded',
    'recorded 9f1c2e3d4b5a6978 · this tree c236a8db3e201090',
    'compared through git: recorded under another Python',
    'results/c4_seed2.txt: changed since its last commit (2026-09-22T03:02:51+03:00)',
    'Seed 3 · Agents scored with a plant mismatch forced',
    "The file's own lines:",
    forced,
    'last commit a3a048e (2026-09-22T03:02:51+03:00)',
    'from commits c5a5341',
  ]);
  assert.ok(plantView(prov, 'ar').details.includes(iso(forced)), 'a forced line sits in an isolate in Arabic too');
});

test('a forced file quotes its own lines and shows no hash comparison', () => {
  const line = '!! runs_c4/blind_seed0: PLANT MISMATCH';
  const prov = { state: 'forced', reason: null, tag: null, commits: [], files: { 0: file(0, { state: 'forced', forced: [line], tag: null }) } };
  const v = plantView(prov, 'en');
  assert.equal(v.text, 'Agents scored with a plant mismatch forced');
  assert.deepEqual(v.details.slice(0, 2), ["The file's own lines:", line]);
  assert.ok(!v.details.some(d => d.startsWith('recorded ')), 'a forced file never reads as a comparison');
  assert.equal(plantView(prov, 'ar').details[1], iso(line));
});

test('the git route, the reasons and a changed file are each said', () => {
  const routed = { ...PROV, state: 'same_code', tag: null, files: { 0: file(0, { route: 'git', state: 'same_code' }) } };
  assert.ok(plantView(routed, 'en').details.includes('compared through git: recorded under another Python'));
  const why = { ...PROV, state: 'another', reason: 'derived_differs' };
  assert.ok(plantView(why, 'en').details.includes('the derived constants differ'));
  const changed = { ...PROV, files: { 0: file(0, { file: { rel: 'results/c4_seed0.txt', commit: { short: 'a3a048e', date: '2026-09-22T03:02:51+03:00' }, changed: true } }) } };
  const details = plantView(changed, 'en').details;
  assert.ok(details.includes('results/c4_seed0.txt: changed since its last commit (2026-09-22T03:02:51+03:00)'));
  assert.ok(!details.some(d => d.startsWith('last commit')), 'a changed file never shows its last commit as a fact about it');
  const untracked = { ...PROV, files: { 0: file(0, { file: { rel: 'results/c4_seed0.txt', commit: null, changed: true } }) } };
  assert.ok(plantView(untracked, 'en').details.includes(`results/c4_seed0.txt: changed since its last commit (${EM_DASH})`));
});

test('a found verdict quotes its lines with file and line, a range for several lines', () => {
  const v = verdictView(VERDICT, 'en');
  assert.equal(v.state, 'found');
  assert.equal(v.short, 'smaller than the MEI (50) at 300 000 steps');
  assert.deepEqual(v.cells, [{ cell: 'SMALLER THAN THE MEI', gloss: 'Preview effect below the threshold' }]);
  assert.deepEqual(v.lines, [
    { cite: 'results/C4_RESULT.txt:40', text: '  RESULT: SMALLER THAN THE MEI' },
    { cite: 'results/C4_RESULT.txt:30-32', text: 'a\nb\nc' },
  ]);
  assert.equal(verdictView(VERDICT, 'ar').short, 'نص قصير');
});

test('no verdict and an unreadable verdict say so in this tab\'s words, never the catalog\'s', () => {
  const none = verdictView({ state: 'none', lines: [], missing: [], short: null, cells: [] }, 'en');
  assert.equal(none.short, 'No verdict recorded for this experiment');
  assert.equal(verdictView({ state: 'unavailable' }, 'en').short, 'The verdict could not be read here.');
  assert.equal(verdictView(undefined, 'en').state, 'unavailable');
  const missing = { state: 'missing', lines: [], missing: ['C4_RESULT.txt'], cells: [],
    short: { ar: 'م', en: 'verdict line not found in results/C4_RESULT.txt: do not read these agents without it' } };
  assert.equal(verdictView(missing, 'en').short, missing.short.en);
  for (const lang of ['ar', 'en']) {
    assert.doesNotMatch(none.short + verdictView({ state: 'none', short: null }, lang).short, /Nothing on this page is a result/);
  }
});

test('notes are filled from their values, numbers as the files record them', () => {
  const notes = [
    { key: 'budget_from_file', values: { steps: 300000 } },
    { key: 'dt_mismatch', values: { train_dt: 0.2, eval_dt: 1 } },
    { key: 'knock_model', values: {} },
  ];
  assert.deepEqual(noteItems(notes, 'en'), [
    `Trained for 300${NNBSP}000 steps, as these files' model lines record.`,
    'Trained at a 0.2 s step and scored at 1 s, as these files\' note lines record.',
    'The margin over current-grade rests on the knock model, which has not been tested on the car (drive C; conflict.md, section 3a, 30 September).',
  ]);
  const ar = noteItems(notes, 'ar');
  assert.equal(ar[0], t('ar', 'results.note.budget_from_file', { steps: iso(`300${NNBSP}000`) }));
  assert.equal(ar[1], t('ar', 'results.note.dt_mismatch', { train_dt: iso('0.2'), eval_dt: iso('1') }));
  assert.deepEqual(noteItems([{ key: 'not_a_note', values: {} }], 'en'), ['results.note.not_a_note']);
  assert.deepEqual(noteItems(undefined, 'en'), []);
});

test('the summary has one row per section: name, plant, short verdict, marks', () => {
  const payload = { sections: [
    section('phase_d', { verdict: { state: 'none', lines: [], missing: [], short: null, cells: [] } }),
    section('d2'),
    section('c4', { continues: 'd2' }),
    { id: 'exp-zz', kind: 'evaluation', state: 'unavailable', prefix: 'zz', name: null, order: 100,
      error: { kind: 'build', file: null, command: null, type: 'ValueError', module: null } },
  ] };
  assert.deepEqual(summaryRows(payload, 'en'), [
    { id: 'exp-phase_d', name: 'Phase D', plant: 'Made on another plant', verdict: 'No verdict recorded for this experiment', markers: [] },
    { id: 'exp-d2', name: 'Phase D2', plant: 'Made on another plant', verdict: VERDICT.short.en, markers: [] },
    { id: 'exp-c4', name: 'C4', plant: 'Made on another plant', verdict: VERDICT.short.en,
      markers: ["Continues Phase D2's agents, on the same episodes"] },
    { id: 'exp-zz', name: 'zz (no name recorded)', plant: EM_DASH, verdict: 'Could not build this section: ValueError', markers: [] },
  ]);
  const ar = summaryRows(payload, 'ar');
  assert.equal(ar[2].markers[0], t('ar', 'results.summary.continues', { other: iso('Phase D2') }));
  assert.equal(ar[0].verdict, t('ar', 'results.summary.no_verdict'));
  assert.deepEqual(summaryRows({}, 'en'), []);
});

test('an unavailable section names a command only when its file is missing', () => {
  assert.equal(unavailableText({ kind: 'missing', file: 'results/c4_seed0.txt', command: 'python run_phase_d.py' }, 'en'),
    'Not available: results/c4_seed0.txt is missing. The command that makes it: python run_phase_d.py');
  assert.equal(unavailableText({ kind: 'read', file: 'results/c4_seed0.txt', type: 'UnicodeDecodeError', command: 'x' }, 'en'),
    'Could not read results/c4_seed0.txt: UnicodeDecodeError');
  assert.equal(unavailableText({ kind: 'module', module: 'evaluate' }, 'en'), 'Needs evaluate, which could not be loaded.');
  assert.equal(unavailableText({ kind: 'build', type: 'SystemExit' }, 'en'), 'Could not build this section: SystemExit');
  assert.equal(unavailableText(null, 'en'), `Could not build this section: ${EM_DASH}`);
  assert.equal(unavailableText({ kind: 'module', module: 'evaluate' }, 'ar'),
    t('ar', 'results.section.unavailable.module', { module: iso('evaluate') }));
});

test('files not read keep their path and say why', () => {
  assert.deepEqual(notReadItems([
    { path: 'results/Bad_seed0.txt', reason: 'name', type: null },
    { path: 'results/x_seed1.txt', reason: 'unreadable', type: 'UnicodeDecodeError' },
    { path: 'results/y_seed2.txt', reason: 'weird', type: null },
  ], 'en'), [
    { path: 'results/Bad_seed0.txt', reason: 'the name is not <prefix>_seed<N>.txt' },
    { path: 'results/x_seed1.txt', reason: 'could not be read (UnicodeDecodeError)' },
    { path: 'results/y_seed2.txt', reason: 'weird' },
  ]);
  assert.deepEqual(notReadItems(undefined, 'en'), []);
});

test('the build line and every warning above the summary', () => {
  const built = { head: '031ed24', python: '3.12.10', plant_sha: 'c236a8db3e201090', restart_needed: false,
    derived_loaded_differs: false, git: 'ok', elapsed_ms: 412 };
  assert.deepEqual(builtView(built, [], 'en'),
    { line: 'Read from commit 031ed24 · Python 3.12.10 · plant c236a8db3e201090', warnings: [] });
  const bad = builtView({ ...built, head: null, git: 'unavailable', restart_needed: true, derived_loaded_differs: true },
    [{ module: 'app.agent_catalog', type: 'AssertionError' }], 'en');
  assert.equal(bad.line, `Read from commit ${EM_DASH} · Python 3.12.10 · plant c236a8db3e201090`);
  assert.deepEqual(bad.warnings, [
    'git is not available here, so the commit facts are left out.',
    'The plant files changed after the server started: restart the server.',
    'The derived constants changed after the server started: restart the server.',
    'Could not load app.agent_catalog (AssertionError). Every section that needs it says so.',
  ]);
  assert.equal(builtView(built, [], 'ar').line,
    t('ar', 'results.built.line', { head: iso('031ed24'), python: iso('3.12.10'), plant: iso('c236a8db3e201090') }));
});

test('cross-checks say pass, fail with the detail, or not compared', () => {
  assert.deepEqual(checkItems([
    { name: 'parse_equals_analysis', state: 'pass', detail: null },
    { name: 'parse_equals_analysis', state: 'fail', detail: 'seed 3 sighted 359.9 != 360.0' },
    { name: 'parse_equals_analysis', state: 'not_compared', detail: null },
    { name: 'unknown_check', state: 'pass', detail: null },
  ], 'en'), [
    "The medians read here equal analyse_phase_d.parse's.",
    "The medians read here differ from analyse_phase_d.parse's: seed 3 sighted 359.9 != 360.0",
    'Not compared with analyse_phase_d.parse.',
    'unknown_check: pass',
  ]);
});

test('unpaired seeds, the thermal-only note and the MEI lines', () => {
  assert.deepEqual(unpairedItems([{ seed: 3, file: 'results/c4_seed3.txt', have: ['baseline', 'reactive', 'sighted'] }], 'en'),
    ['Seed 3 has no pair (Sighted agent); it is not drawn.']);
  assert.deepEqual(unpairedItems([{ seed: 4, have: ['baseline'] }], 'en'), [`Seed 4 has no pair (${EM_DASH}); it is not drawn.`]);
  assert.equal(thermalNote(section('c4', { thermal_recorded: 'none' }), 'en'), 'Damage without the knock term: not recorded in these files.');
  assert.equal(thermalNote(section('c4', { thermal_recorded: 'all' }), 'en'), null);
  const some = section('c4', { thermal_recorded: 'some', seeds: [
    { seed: 0, thermal: { sighted: { median: 1 }, blind: { median: 2 } } },
    { seed: 1, thermal: null },
    { seed: 2, thermal: { sighted: { median: 1 }, blind: { median: 2 } } },
  ] });
  assert.equal(thermalNote(some, 'en'), 'Without the knock term only for seeds 0, 2; the others did not record it.');
  assert.deepEqual(meiLines(section('phase_d', { mei_after_result: true }), 'en'), [
    'The bracket is the minimum effect of interest, 50 damage units.',
    'It was set on 22 September, after this result.',
  ]);
  assert.deepEqual(meiLines(section('d2'), 'en'), ['The bracket is the minimum effect of interest, 50 damage units.']);
  assert.deepEqual(meiLines(section('d2', { mei: null }), 'en'), []);
});

test('negative numbers keep U+2212 and every Arabic value sits in an isolate', () => {
  assert.deepEqual(noteItems([{ key: 'dt_mismatch', values: { train_dt: -0.5, eval_dt: 1 } }], 'en'),
    [`Trained at a ${MINUS}0.5 s step and scored at 1 s, as these files' note lines record.`]);
  const ar = noteItems([{ key: 'budget_from_file', values: { steps: 300000 } }], 'ar')[0];
  assert.ok(ar.includes(iso(`300${NNBSP}000`)), ar);
});

test('nothing the view writes uses a banned word or says preview helps, in either language', () => {
  const payload = { sections: [section('phase_d', { notes: [{ key: 'knock_model', values: {} }] }), section('c4', { continues: 'phase_d' })] };
  const out = [];
  for (const lang of ['ar', 'en']) {
    for (const row of summaryRows(payload, lang)) out.push(row.name, row.plant, row.verdict, ...row.markers);
    out.push(...plantView(PROV, lang).details, ...noteItems(payload.sections[0].notes, lang),
      builtView({ git: 'unavailable', restart_needed: true, derived_loaded_differs: true }, [], lang).warnings.join(' '));
  }
  const text = out.join('\n').replace(/current-grade/gi, '');
  assert.doesNotMatch(text, /\b(current|stale|outdated|fresh)\b|up to date|preview (does not |doesn't )?help/i);
  assert.doesNotMatch(text, /حديث|قديم|محدَّث|محدث|الاستباق يساعد|يساعد الاستباق|الاستباق لا يفيد|لا يفيد الاستباق|الاستباق لا يساعد/);
});

test('the view carries no literal invisible character', () => {
  const banned = [0x2066, 0x2067, 0x2068, 0x2069, 0x200f, 0x200e, 0x202f, 0x2212, 0x2011];
  const src = readFileSync(new URL('./results-view.mjs', import.meta.url), 'utf8');
  const found = [...src].filter(c => banned.includes(c.codePointAt(0))).map(c => c.codePointAt(0).toString(16));
  assert.deepEqual(found, [], 'results-view.mjs holds literal invisible characters');
});
