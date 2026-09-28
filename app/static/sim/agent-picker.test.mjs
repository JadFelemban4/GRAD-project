// The picker's pure logic, driven by the catalog the server really serves.
//
// agent-catalog.fixture.json is GENERATED, never edited by hand: it is
// app/agent_api.py catalog(sb3=True) written as ASCII JSON with sorted keys,
// sb3 pinned true so the file does not depend on the machine. It holds the
// repository's four runs directories: runs, runs_c4, runs_d2 and
// runs_sixspeed_18sep. After any change to the catalog's shape
// (app/test_agents.py PageTests.test_catalog_fixture_has_the_server_shape
// fails first), regenerate it from the repository root, in Git Bash:
//   $PY -c "import json; from app import agent_api as API; cat = API.catalog(sb3=True); fh = open('app/static/sim/agent-catalog.fixture.json', 'w', encoding='utf-8', newline=''); json.dump(cat, fh, indent=1, sort_keys=True, ensure_ascii=True, allow_nan=False); fh.write(chr(10)); fh.close(); print([(e['runs'], len(e['pairs'])) for e in cat['experiments']])"
import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { t } from './i18n.mjs';
import './agents-strings.mjs';
import * as P from './agent-picker.mjs';

const CATALOG = JSON.parse(readFileSync(new URL('./agent-catalog.fixture.json', import.meta.url), 'utf8'));
const LRI = String.fromCodePoint(0x2066);
const PDI = String.fromCodePoint(0x2069);
const MINUS = String.fromCodePoint(0x2212);
const FULL = { runs: 'runs_c4', seed: 5, ep: 1 };

// A copy of the fixture with one C4 pair refused and one experiment that holds
// no pair: the two cases the real tree does not have today.
function withRefusals() {
  const cat = structuredClone(CATALOG);
  const pair = P.pairOf(P.experimentOf(cat, 'runs_c4'), 3);
  pair.runnable = false;
  pair.protocol = null;
  pair.reason = 'blind_seed3: incomplete -- final.zip is not a readable stable-baselines3 zip';
  pair.problems = [pair.reason];
  cat.experiments.push({
    runs: 'runs_zzempty', name: 'runs_zzempty (no name recorded)', prefix: 'zzempty', protocol: null,
    verdict: { state: 'none', lines: [], missing: [], short: null, cells: [] }, pairs: [],
  });
  return cat;
}

test('the address is read level by level, only by the server\'s own patterns', () => {
  assert.deepEqual(P.parsePickerQuery('?runs=runs_c4&seed=5&ep=1'), FULL);
  assert.deepEqual(P.parsePickerQuery(''), P.NOTHING);
  assert.deepEqual(P.parsePickerQuery(undefined), P.NOTHING);
  assert.deepEqual(P.parsePickerQuery('?runs=runs_c4'), { runs: 'runs_c4', seed: null, ep: null });
  assert.deepEqual(P.parsePickerQuery('?runs=runs_c4&seed=5'), { runs: 'runs_c4', seed: 5, ep: null });
  assert.deepEqual(P.parsePickerQuery('?runs=runs_c4&seed=5&ep=21'), { runs: 'runs_c4', seed: 5, ep: null });
  assert.deepEqual(P.parsePickerQuery('?runs=runs_c4&seed=5&ep=0'), { runs: 'runs_c4', seed: 5, ep: null });
  assert.deepEqual(P.parsePickerQuery('?runs=runs_C4&seed=5&ep=1'), P.NOTHING);
  assert.deepEqual(P.parsePickerQuery('?runs=../x&seed=5&ep=1'), P.NOTHING);
  assert.deepEqual(P.parsePickerQuery('?seed=5&ep=1'), P.NOTHING);
  assert.deepEqual(P.parsePickerQuery('?runs=runs_c4&seed=5abc&ep=1'), { runs: 'runs_c4', seed: null, ep: null });
  assert.deepEqual(P.parsePickerQuery('?runs=runs_c4&ep=1'), { runs: 'runs_c4', seed: null, ep: null });
  assert.ok(Object.isFrozen(P.NOTHING));
});

test('an address selects only what exists and can run; nothing is ever chosen for the viewer', () => {
  assert.deepEqual(P.resolveSelection(CATALOG, P.NOTHING), P.NOTHING);
  assert.deepEqual(P.resolveSelection(CATALOG, FULL), FULL);
  assert.deepEqual(P.resolveSelection(CATALOG, { runs: 'runs', seed: 0, ep: 20 }), { runs: 'runs', seed: 0, ep: 20 });
  assert.deepEqual(P.resolveSelection(CATALOG, { runs: 'runs_zz', seed: 5, ep: 1 }), P.NOTHING);
  assert.deepEqual(P.resolveSelection(CATALOG, { runs: 'runs_c4', seed: 99, ep: 1 }), { runs: 'runs_c4', seed: null, ep: null });
  assert.deepEqual(P.resolveSelection(CATALOG, { runs: 'runs_c4', seed: 5, ep: null }), { runs: 'runs_c4', seed: 5, ep: null });
  assert.deepEqual(P.resolveSelection(CATALOG, { runs: 'runs_sixspeed_18sep', seed: 0, ep: 1 }), P.NOTHING);
  assert.deepEqual(P.resolveSelection(null, FULL), P.NOTHING);
  assert.deepEqual(P.resolveSelection(CATALOG, { runs: 'runs_c4', seed: null, ep: null }), { runs: 'runs_c4', seed: null, ep: null });
  const refused = withRefusals();
  assert.deepEqual(P.resolveSelection(refused, { runs: 'runs_c4', seed: 3, ep: 1 }), { runs: 'runs_c4', seed: null, ep: null });
  assert.deepEqual(P.resolveSelection(refused, { runs: 'runs_zzempty', seed: 0, ep: 1 }), P.NOTHING);
  // Whole addresses, as a reload or a shared link brings them: only a full,
  // runnable one can make «احسب» possible, and none of them computes by itself.
  for (const [search, want] of [
    ['', P.NOTHING],
    ['?runs=runs_sixspeed_18sep&seed=0&ep=1', P.NOTHING],
    ['?runs=runs_zz&seed=5&ep=1', P.NOTHING],
    ['?runs=runs_C4&seed=5&ep=1', P.NOTHING],
    ['?runs=runs_c4&seed=99&ep=1', { runs: 'runs_c4', seed: null, ep: null }],
    ['?runs=runs_c4&seed=5&ep=21', { runs: 'runs_c4', seed: 5, ep: null }],
    ['?runs=runs_c4&seed=5&ep=1', FULL],
  ]) {
    const sel = P.resolveSelection(CATALOG, P.parsePickerQuery(search));
    assert.deepEqual(sel, want, search);
    assert.equal(P.computeState({ ...CATALOG, sb3: true }, sel).ok, search === '?runs=runs_c4&seed=5&ep=1', search);
  }
});

test('choosing clears what depends on it, and keeps the episode only across pairs of one protocol', () => {
  let sel = P.choose(CATALOG, P.NOTHING, 'runs', 'runs_c4');
  assert.deepEqual(sel, { runs: 'runs_c4', seed: null, ep: null });
  sel = P.choose(CATALOG, sel, 'seed', '5');
  assert.deepEqual(sel, { runs: 'runs_c4', seed: 5, ep: null });
  sel = P.choose(CATALOG, sel, 'ep', '7');
  assert.deepEqual(sel, { runs: 'runs_c4', seed: 5, ep: 7 });
  assert.deepEqual(P.choose(CATALOG, sel, 'seed', '3'), { runs: 'runs_c4', seed: 3, ep: 7 });
  assert.deepEqual(P.choose(CATALOG, sel, 'seed', '5'), sel);
  assert.deepEqual(P.choose(CATALOG, sel, 'runs', 'runs_d2'), { runs: 'runs_d2', seed: null, ep: null });
  assert.deepEqual(P.choose(CATALOG, sel, 'runs', ''), P.NOTHING);
  assert.deepEqual(P.choose(CATALOG, sel, 'seed', ''), { runs: 'runs_c4', seed: null, ep: null });
  assert.deepEqual(P.choose(CATALOG, sel, 'seed', '99'), { runs: 'runs_c4', seed: null, ep: null });
  assert.deepEqual(P.choose(CATALOG, sel, 'ep', ''), { runs: 'runs_c4', seed: 5, ep: null });
  assert.deepEqual(P.choose(CATALOG, sel, 'ep', '21'), { runs: 'runs_c4', seed: 5, ep: null });
  assert.deepEqual(P.choose(CATALOG, sel, 'runs', 'runs_sixspeed_18sep'), P.NOTHING);
  assert.deepEqual(P.choose(CATALOG, { runs: 'runs_c4', seed: null, ep: null }, 'ep', '1'), { runs: 'runs_c4', seed: null, ep: null });
  assert.deepEqual(P.choose(null, sel, 'seed', '3'), P.NOTHING);
  // A refused pair cannot be chosen, even by a script that ignores `disabled`.
  assert.deepEqual(P.choose(withRefusals(), sel, 'seed', '3'), { runs: 'runs_c4', seed: null, ep: null });
  // A pair scored on another protocol does not inherit the episode number.
  const mixed = structuredClone(CATALOG);
  P.pairOf(P.experimentOf(mixed, 'runs_c4'), 3).protocol = 'phase-d';
  assert.deepEqual(P.choose(mixed, sel, 'seed', '3'), { runs: 'runs_c4', seed: 3, ep: null });
});

test('the address follows the selection and never says more than was chosen', () => {
  assert.equal(P.selectionSearch(P.NOTHING), '');
  assert.equal(P.selectionSearch(undefined), '');
  assert.equal(P.selectionSearch({ runs: 'runs_c4', seed: null, ep: 4 }), '?runs=runs_c4');
  assert.equal(P.selectionSearch({ runs: 'runs_c4', seed: 5, ep: null }), '?runs=runs_c4&seed=5');
  assert.equal(P.selectionSearch(FULL), '?runs=runs_c4&seed=5&ep=1');
  assert.equal(P.selectionSearch({ runs: 'runs', seed: 0, ep: 20 }), '?runs=runs&seed=0&ep=20');
  for (const sel of [FULL, { runs: 'runs', seed: 0, ep: null }, { runs: 'runs_d2', seed: null, ep: null }, P.NOTHING]) {
    assert.deepEqual(P.resolveSelection(CATALOG, P.parsePickerQuery(P.selectionSearch(sel))), sel);
  }
});

test('«احسب» needs a runnable pair, an episode and stable-baselines3', () => {
  const on = { ...CATALOG, sb3: true };
  const off = { ...CATALOG, sb3: false };
  assert.deepEqual(P.computeState(null, FULL), { ok: false, reason: 'agents.pick.catalog_loading' });
  assert.deepEqual(P.computeState(on, P.NOTHING), { ok: false, reason: 'agents.pick.none' });
  assert.deepEqual(P.computeState(on, { runs: 'runs_c4', seed: null, ep: null }), { ok: false, reason: 'agents.pick.need_pair' });
  assert.deepEqual(P.computeState(on, { runs: 'runs_c4', seed: 5, ep: null }), { ok: false, reason: 'agents.pick.need_episode' });
  assert.deepEqual(P.computeState(on, { runs: 'runs_c4', seed: 5, ep: 21 }), { ok: false, reason: 'agents.pick.need_episode' });
  assert.deepEqual(P.computeState(on, FULL), { ok: true, reason: null });
  // Without stable-baselines3 no pair can ever run, so that is the reason from
  // the moment the catalog arrives, whatever has been chosen so far.
  for (const sel of [P.NOTHING, { runs: 'runs_c4', seed: null, ep: null }, { runs: 'runs_c4', seed: 5, ep: null }, FULL]) {
    assert.deepEqual(P.computeState(off, sel), { ok: false, reason: 'agents.load.no_sb3' }, JSON.stringify(sel));
  }
  const reasons = [P.computeState(null, FULL), P.computeState(on, P.NOTHING), P.computeState(on, { runs: 'runs_c4', seed: null, ep: null }),
    P.computeState(on, { runs: 'runs_c4', seed: 5, ep: null }), P.computeState(off, FULL)].map(s => s.reason);
  for (const reason of reasons) {
    for (const lang of ['ar', 'en']) assert.notEqual(t(lang, reason), reason, `${reason} has no ${lang} string`);
  }
});

test('a table row is signed, one decimal, in a left-to-right isolate', () => {
  assert.equal(P.formatDiff(360.6), `${LRI}+360.6${PDI}`);
  assert.equal(P.formatDiff(-80.3), `${LRI}${MINUS}80.3${PDI}`);
  assert.equal(P.formatDiff(0), `${LRI}+0.0${PDI}`);
  assert.equal(P.formatDiff(-0.04), `${LRI}+0.0${PDI}`);
  assert.equal(P.formatDiff(null), '—');
  assert.equal(P.formatDiff(Number.NaN), '—');
  assert.equal(P.formatDiff('360.6'), '—');
});

test('the three selects list every experiment, every pair and the twenty episodes, in both languages, with no raw key or unfilled slot', () => {
  const refused = withRefusals();
  for (const lang of ['ar', 'en']) {
    const exps = P.experimentOptions(CATALOG, lang);
    assert.deepEqual(exps[0], { value: '', text: t(lang, 'agents.pick.choose'), disabled: false });
    assert.deepEqual(exps.slice(1).map(o => o.value), ['runs', 'runs_c4', 'runs_d2', 'runs_sixspeed_18sep']);
    assert.deepEqual(exps.slice(1).map(o => o.disabled), [false, false, false, true]);
    assert.match(exps[4].text, /no meta\.json/);
    const c4 = P.experimentOf(CATALOG, 'runs_c4');
    assert.equal(exps[2].text, `C4 · ${c4.verdict.short[lang]}`);
    const empty = P.experimentOptions(refused, lang).find(o => o.value === 'runs_zzempty');
    assert.equal(empty.disabled, true);
    assert.equal(empty.text, t(lang, 'agents.pick.experiment_empty', { name: 'runs_zzempty (no name recorded)' }));

    const pairs = P.pairOptions(c4, lang);
    assert.equal(pairs.length, 9);
    assert.deepEqual(pairs.slice(1).map(o => o.value), ['0', '1', '2', '3', '4', '5', '6', '7']);
    assert.ok(pairs[1].text.includes(`${LRI}+360.6${PDI}`), pairs[1].text);
    assert.ok(pairs[2].text.includes(`${LRI}${MINUS}80.3${PDI}`), pairs[2].text);
    const three = P.pairOptions(P.experimentOf(refused, 'runs_c4'), lang)[4];
    assert.equal(three.disabled, true);
    assert.match(three.text, /final\.zip is not a readable/);

    const eps = P.episodeOptions(CATALOG, P.pairOf(c4, 5), lang);
    assert.equal(eps.length, 21);
    assert.deepEqual(eps.slice(1).map(o => o.value), Array.from({ length: 20 }, (_, i) => String(i + 1)));
    for (const bit of ['141', '13.3', '0.69', '0.01', '0.30']) assert.ok(eps[1].text.includes(bit), `${bit} not in ${eps[1].text}`);

    const pd = P.pairOf(P.experimentOf(CATALOG, 'runs'), 0);
    const pdEps = P.episodeOptions(CATALOG, pd, lang);
    assert.equal(pdEps.length, 21);
    CATALOG.episodes.d2.forEach((e, i) => {
      assert.ok(!pdEps[i + 1].text.includes(e.climb_start_s.toFixed(0)), `Phase D episode ${e.idx} names a D2 climb start`);
      assert.ok(pdEps[i + 1].text.includes(lang === 'ar' ? 'الطريق نفسه' : 'same road'), pdEps[i + 1].text);
    });
    assert.deepEqual(P.episodeOptions(CATALOG, null, lang).length, 1);
    assert.deepEqual(P.episodeOptions(refused, P.pairOf(P.experimentOf(refused, 'runs_c4'), 3), lang).length, 1);

    for (const o of [...exps, ...pairs, ...eps, ...pdEps]) {
      assert.doesNotMatch(o.text, /[{][a-z0-9_]+[}]/i, `${lang}: an unfilled placeholder in ${o.text}`);
      assert.ok(!o.text.startsWith('agents.'), `${lang}: a raw key ${o.text}`);
    }
  }
});

// A greyed option has room for one line, but design section 8 lists a refused
// agent "with reason and fields": the page must be able to show EVERY problem
// of both arms. And the catalog's 'scored' takes three values (Task 3), the
// third being a zip sha that differs from the one results/ records.
test('a refused pair keeps every problem of both arms, and every scored value has a label', () => {
  const six = P.experimentOf(CATALOG, 'runs_sixspeed_18sep');
  assert.deepEqual(P.refusedPairs(CATALOG), [
    { runs: 'runs_sixspeed_18sep', name: six.name, seed: 0, problems: six.pairs[0].problems },
  ]);
  assert.deepEqual(P.refusedPairs(CATALOG)[0].problems.map(line => line.split(':')[0]), ['sighted_seed0', 'blind_seed0']);
  assert.deepEqual(P.refusedPairs(null), []);

  // A C4 pair refused because neither final.zip is the scored one.
  const cat = structuredClone(CATALOG);
  const pair = P.pairOf(P.experimentOf(cat, 'runs_c4'), 3);
  const lines = pair.agents.map(a => `${a.tag}: not the scored artefact -- results/c4_seed3.txt records zip sha 0000000000000000, final.zip is ${a.zip_sha}`);
  Object.assign(pair, { runnable: false, protocol: null, reason: lines[0], problems: lines });
  for (const a of pair.agents) a.scored = 'mismatch';
  assert.deepEqual(P.refusedPairs(cat).map(r => [r.runs, r.seed, r.problems]),
    [['runs_c4', 3, lines], ['runs_sixspeed_18sep', 0, six.pairs[0].problems]]);
  for (const lang of ['ar', 'en']) {
    const option = P.pairOptions(P.experimentOf(cat, 'runs_c4'), lang)[4];
    assert.equal(option.disabled, true);
    assert.ok(option.text.includes(lines[0]) && !option.text.includes(lines[1]), `the greyed option stays one line: ${option.text}`);
  }

  assert.equal(P.scoredKey('match', true), 'agents.verdict.scored_match');
  assert.equal(P.scoredKey('not recorded', true), 'agents.verdict.not_recorded');
  assert.equal(P.scoredKey('mismatch', true), 'agents.verdict.scored_mismatch');
  assert.equal(P.scoredKey('match', false), 'agents.verdict.no_result');
  assert.equal(P.scoredKey(null, true), null, 'the sha check never ran: nothing to say');
  assert.equal(P.scoredKey('constructor', true), null);
  for (const key of ['agents.verdict.scored_match', 'agents.verdict.not_recorded', 'agents.verdict.scored_mismatch', 'agents.verdict.no_result']) {
    for (const lang of ['ar', 'en']) assert.notEqual(t(lang, key), key, `${key} has no ${lang} string`);
  }
  for (const lang of ['ar', 'en']) {
    assert.notEqual(t(lang, 'agents.verdict.scored_mismatch'), t(lang, 'agents.verdict.not_recorded'));
  }
  // On the real tree every agent of every runnable pair has something to say.
  for (const e of CATALOG.experiments) {
    for (const p of e.pairs.filter(q => q.runnable)) {
      for (const a of p.agents) assert.notEqual(P.scoredKey(a.scored, p.result_file), null, `${e.runs} ${a.tag}`);
    }
  }
});

test('Phase D reads as one road, and its blind car keeps its caveat, cited where results/ says it', () => {
  const phaseD = P.experimentOf(CATALOG, 'runs');
  const c4 = P.experimentOf(CATALOG, 'runs_c4');
  const six = P.experimentOf(CATALOG, 'runs_sixspeed_18sep');
  for (const lang of ['ar', 'en']) {
    const note = P.sameRoadNote(CATALOG, phaseD, lang);
    assert.ok(note.includes('180') && note.includes('12.0'), note);
    assert.equal(P.sameRoadNote(CATALOG, c4, lang), '');
    assert.equal(P.sameRoadNote(CATALOG, null, lang), '');
    assert.equal(P.pairQualifier(phaseD, lang), t(lang, 'agents.pick.pair_qualifier_same_road'));
    assert.equal(P.pairQualifier(c4, lang), t(lang, 'agents.pick.pair_qualifier'));
    assert.notEqual(P.pairQualifier(phaseD, lang), P.pairQualifier(c4, lang));
    assert.equal(P.pairQualifier(six, lang), '');
  }
  assert.equal(P.blindLabelKey('phase-d'), 'agents.car.blind_phase_d');
  assert.equal(P.blindLabelKey('d2'), 'agents.car.blind');
  assert.equal(P.blindLabelKey(undefined), 'agents.car.blind');
  assert.equal(P.notBlindCite(phaseD.verdict), 'results/PHASE_D_RESULT.txt:33-40');
  assert.equal(P.notBlindCite(c4.verdict), 'results/PHASE_D_RESULT.txt');
  assert.equal(P.notBlindCite(null), 'results/PHASE_D_RESULT.txt');
  assert.match(t('ar', P.blindLabelKey('phase-d')), /قد يحفظه/);
  assert.match(t('en', P.blindLabelKey('phase-d')), /memorised/);
  assert.doesNotMatch(t('ar', P.blindLabelKey('d2')), /قد يحفظه/);
});

// Design section 6 names the experiment select as a surface of "C4 is a clean
// negative", but a CLOSED select shows only as much of its option as fits. On
// 28 Sep at 390 px it read «C4 · أصغر من الحد الأدنى المهم (50 وحدة) عند 300 000
// خطوة», the clean negative itself, and at 1440 px it stopped inside «بفارق بذرة
// واحدة». So the chosen experiment's WHOLE short line is said under the select.
test('the chosen experiment\'s whole short line is said under its select, every qualifier with it', () => {
  const clauses = {
    ar: ['بفارق بذرة واحدة', 'الاختباران لا يتفقان', 'لم يستقر التدريب'],
    en: ['one seed wide', 'the two tests disagree', 'not converged'],
  };
  const empty = withRefusals().experiments.find(e => e.runs === 'runs_zzempty');
  for (const lang of ['ar', 'en']) {
    const c4 = P.experimentOf(CATALOG, 'runs_c4');
    const note = P.experimentNote(c4, lang);
    assert.equal(note, c4.verdict.short[lang], `${lang}: the line the verdict box prints, whole`);
    for (const clause of clauses[lang]) assert.ok(note.includes(clause), `${lang}: «${clause}» not in ${note}`);
    for (const runs of ['runs', 'runs_d2']) {
      const e = P.experimentOf(CATALOG, runs);
      assert.equal(P.experimentNote(e, lang), e.verdict.short[lang], `${lang}: ${runs}`);
    }
    assert.equal(P.experimentNote(null, lang), '', 'nothing chosen, nothing said');
    assert.equal(P.experimentNote(empty, lang), '', 'no short line, so nothing is guessed');
  }
});

test('the fixture is the server\'s catalog', () => {
  assert.deepEqual(CATALOG.experiments.map(e => [e.runs, e.pairs.length]),
    [['runs', 8], ['runs_c4', 8], ['runs_d2', 8], ['runs_sixspeed_18sep', 1]]);
  assert.deepEqual(CATALOG.experiments.map(e => e.protocol), ['phase-d', 'd2', 'd2', null]);
  assert.equal(P.pairOf(P.experimentOf(CATALOG, 'runs_c4'), 0).table_diff, 360.6);
  assert.equal(CATALOG.sb3, true);
  for (const protocol of ['d2', 'phase-d']) {
    assert.deepEqual(CATALOG.episodes[protocol].map(e => e.idx), Array.from({ length: 20 }, (_, i) => i + 1));
  }
  for (const e of CATALOG.episodes['phase-d']) {
    assert.equal(e.climb_start_s, 180);
    assert.equal(e.grade, 0.12);
  }
  assert.deepEqual(CATALOG.episodes.d2[0], {
    climb_start_s: 141, grade: 0.13314, idx: 1, seed: 1000, weights: [0.690154, 0.012829, 0.297017],
  });
});
