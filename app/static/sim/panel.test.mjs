import test from 'node:test';
import assert from 'node:assert/strict';
import {
  gearState, horizonRatio, previewCaption, thin, channelPath, cursorY, cursorX,
  EM_DASH, CHART_H, PAD_Y, thresholdState, thresholdSpans,
} from './panel.mjs';
import { STRINGS, LANGS } from './i18n.mjs';

test('a clipped channel lights the inferred gear and says it is estimated', () => {
  // replay.infer_gear(1944.59, 120, 6) -> gear 8, estimated, note clipped_channel
  const s = gearState({ gear: 8, gear_source: 'estimated', gear_note: 'clipped_channel', ratio_error: 0.004 });
  assert.equal(s.gear, 8);
  assert.equal(s.estimated, true);
  assert.equal(s.sourceText, 'مقدّر');
  assert.match(s.note, /متشبّعة عند 6/);
  assert.match(s.note, /0\.4٪/);
});

test('a checked recorded gear is not labelled estimated', () => {
  const s = gearState({ gear: 3, gear_source: 'recorded', gear_note: 'recorded_ratio_checked', ratio_error: 0.01 });
  assert.equal(s.gear, 3);
  assert.equal(s.estimated, false);
  assert.equal(s.sourceText, 'مسجّل');
});

test('slip, missing data and a sourceless gear never light a cell', () => {
  for (const frame of [
    null,
    { gear: null, gear_source: 'unavailable', gear_note: 'ratio_mismatch_or_slip' },
    { gear: null, gear_source: 'unavailable', gear_note: 'insufficient_data' },
    // A gear with no source must not be trusted either.
    { gear: 7, gear_source: 'unavailable', gear_note: 'ratio_mismatch_or_slip' },
  ]) {
    assert.equal(gearState(frame).gear, null);
  }
  assert.equal(gearState(null).sourceText, 'غير متاح');
});

test('every gear_note replay can emit has a caption in every language', () => {
  // These are exactly the gear_note values app/replay.py:infer_gear can return.
  const notes = ['insufficient_data', 'low_speed_or_slip', 'low_speed_recording',
    'ratio_mismatch_or_slip', 'recorded_ratio_checked',
    'clipped_channel', 'rpm_speed_ratio'];
  for (const lang of LANGS) {
    const fallback = STRINGS[lang]['gear.note.waiting'];
    for (const n of notes) {
      const s = gearState({ gear: 4, gear_source: 'estimated', gear_note: n, ratio_error: null }, lang);
      assert.notEqual(s.note, fallback, `${n} has no ${lang} caption`);
    }
  }
});

test('the gear strip speaks whichever language it is given', () => {
  const frame = { gear: 8, gear_source: 'estimated', gear_note: 'clipped_channel', ratio_error: null };
  assert.equal(gearState(frame, 'ar').sourceText, 'مقدّر');
  assert.equal(gearState(frame, 'en').sourceText, 'Estimated');
  // The gear itself is data and must not move with the language.
  for (const lang of LANGS) assert.equal(gearState(frame, lang).gear, 8);
});

test('every honesty caveat survives translation into both languages', () => {
  // A caveat dropped by a translator is the failure this project punishes most.
  const mustSay = {
    'preview.caption.complete': { ar: /متحكم استباقي/, en: /predictive controller/i },
    'preview.caption.partial': { ar: /متحكم استباقي/, en: /predictive controller/i },
    'seed.model_output': { ar: /ليست قراءة حساس/, en: /not a sensor reading/i },
    'ratio.caveat': { ar: /مفترَضة/, en: /assumed/i },
    'scene.terrain_label': { ar: /ليس مسار GPS/, en: /not a GPS/i },
  };
  for (const [key, langs] of Object.entries(mustSay)) {
    for (const [lang, pattern] of Object.entries(langs)) {
      assert.ok(STRINGS[lang][key], `${key} missing in ${lang}`);
      assert.match(STRINGS[lang][key], pattern, `${key} lost its caveat in ${lang}`);
    }
  }
});

test('both languages define exactly the same keys', () => {
  const [a, b] = LANGS.map(l => Object.keys(STRINGS[l]).sort());
  assert.deepEqual(a, b);
});

test('H/tau divides the chosen horizon by the frame tau, and refuses a bad tau', () => {
  assert.equal(horizonRatio(30, 150).ratioText, '0.20');
  assert.equal(horizonRatio(30, 48).ratioText, '0.63');
  assert.equal(horizonRatio(15, 150).ratioText, '0.10');
  // tau is flow-dependent, so the same H gives a different ratio per sample.
  assert.notEqual(horizonRatio(30, 17.3).ratioText, horizonRatio(30, 191.1).ratioText);
  for (const bad of [null, undefined, NaN, 0, -5, Infinity]) {
    assert.equal(horizonRatio(30, bad).ratioText, EM_DASH);
    assert.equal(horizonRatio(30, bad).tauText, EM_DASH);
  }
});

test('the preview caption never implies a predictive controller is running', () => {
  for (const [lang, re] of [['ar', /متحكم استباقي/], ['en', /predictive controller/i]]) {
    assert.match(previewCaption({ distance_m: 900, covered_s: 30, complete: true }, lang), re);
    assert.match(previewCaption({ distance_m: 120, covered_s: 7, complete: false }, lang), re);
  }
  assert.match(previewCaption({ distance_m: 120, covered_s: 7, complete: false }, 'en'), /7 s/);
  assert.match(previewCaption({ distance_m: null }, 'ar'), /لا مسافة استباق/);
  assert.match(previewCaption(null, 'en'), /No preview distance/i);
});

test('thinning keeps the first and last sample whatever the stride', () => {
  const frames = Array.from({ length: 5000 }, (_, i) => ({ t: i, v: i }));
  const out = thin(frames, 100);
  assert.ok(out.length <= 102, `got ${out.length}`);
  assert.equal(out[0], frames[0]);
  assert.equal(out[out.length - 1], frames[frames.length - 1]);
  const short = thin(frames.slice(0, 40), 100);
  assert.equal(short.length, 40);
});

test('a logger gap lifts the pen instead of drawing a line across the hole', () => {
  const frames = [
    { t: 0, v: 10 }, { t: 1, v: 20 },
    { t: 2, v: 30, gap: true },
    { t: 3, v: 40 },
  ];
  const path = channelPath(frames, 'v', 3);
  // Two M commands: the run before the gap, and the run after it.
  assert.equal((path.d.match(/M/g) || []).length, 2);
});

test('a missing value breaks the line and is never interpolated', () => {
  const path = channelPath([{ t: 0, v: 1 }, { t: 1, v: null }, { t: 2, v: 3 }], 'v', 2);
  assert.equal((path.d.match(/M/g) || []).length, 2);
});

test('a channel absent from the recording produces no path at all', () => {
  assert.equal(channelPath([{ t: 0, v: null }, { t: 1, v: null }], 'v', 1), null);
  assert.equal(channelPath([{ t: 0, v: 5 }], 'v', 1), null);
});

test('a flat channel still renders inside the plot area', () => {
  const path = channelPath([{ t: 0, v: 90 }, { t: 1, v: 90 }, { t: 2, v: 90 }], 'v', 2);
  assert.ok(path, 'a constant coolant trace must still draw');
  const y = cursorY(path, 90, false);
  assert.ok(y > PAD_Y && y < CHART_H - PAD_Y, `y=${y} left the plot area`);
});

test('the cursor dot hides on a gap or a missing value, and clamps in time', () => {
  const path = channelPath([{ t: 0, v: 0 }, { t: 1, v: 100 }], 'v', 1);
  assert.equal(cursorY(path, null, false), null);
  assert.equal(cursorY(path, 50, true), null);
  assert.equal(cursorY(null, 50, false), null);
  assert.ok(Number.isFinite(cursorY(path, 50, false)));
  assert.equal(cursorX(0, 0), cursorX(0, 100));
  assert.ok(cursorX(1e6, 100) <= cursorX(100, 100) + 1e-9);
});

test('the threshold highlight has three states and refuses a missing value', () => {
  // Exact values, so the band edge is asserted rather than approximated.
  assert.equal(thresholdState(700, 850).level, 'normal');
  assert.equal(thresholdState(799, 850).level, 'normal');   // 51 K away
  assert.equal(thresholdState(800, 850).level, 'near');     // exactly 50 K: inclusive
  assert.equal(thresholdState(849, 850).level, 'near');
  assert.equal(thresholdState(850, 850).level, 'over');     // at the threshold counts
  assert.equal(thresholdState(890, 850).over, 40);
  assert.equal(thresholdState(800, 850).margin, 50);
  const L = 849.9;
  for (const bad of [null, undefined, NaN]) {
    assert.equal(thresholdState(bad, L).level, 'none');
    assert.equal(thresholdState(800, bad).level, 'none');
  }
});

test('threshold spans measure time above, and a gap never counts as above', () => {
  const L = 850;
  const frames = [
    { t: 0, turbine_c: 800 },
    { t: 1, turbine_c: 860 },          // span opens
    { t: 2, turbine_c: 870 },
    { t: 3, turbine_c: 800 },          // closes at t=2 -> 1 s
    { t: 4, turbine_c: 900, gap: true },  // hot but unmeasured: not counted
    { t: 5, turbine_c: 900 },          // opens again
    { t: 7, turbine_c: 900 },          // still open at the end -> 2 s
  ];
  const { spans, total_s } = thresholdSpans(frames, L);
  assert.equal(spans.length, 2);
  assert.deepEqual(spans[0], { from: 1, to: 2 });
  assert.deepEqual(spans[1], { from: 5, to: 7 });
  assert.equal(total_s, 3);
});

test('a drive that never reaches the threshold reports no spans at all', () => {
  const frames = [{ t: 0, turbine_c: 600 }, { t: 1, turbine_c: 797.6 }, { t: 2, turbine_c: 700 }];
  const r = thresholdSpans(frames, 849.9);
  assert.equal(r.spans.length, 0);
  assert.equal(r.total_s, 0);
  // and a missing limit must not invent one
  assert.equal(thresholdSpans(frames, null).total_s, 0);
});

test('a node far below the limit but heading above it counts as approaching', () => {
  const L = 850;
  // 600 C is 250 K clear of the limit, so the value band says nothing at all...
  assert.equal(thresholdState(600, L).level, 'normal');
  // ...but if this operating point settles at 900 C, it is on its way there.
  const heading = thresholdState(600, L, 900);
  assert.equal(heading.level, 'near');
  assert.equal(heading.heading, true);
  // A steady state below the limit must not raise anything.
  assert.equal(thresholdState(600, L, 800).level, 'normal');
  assert.equal(thresholdState(600, L, 800).heading, false);
  // Missing steady state degrades to the value band, never to a guess.
  for (const bad of [null, undefined, NaN]) {
    assert.equal(thresholdState(600, L, bad).level, 'normal');
    assert.equal(thresholdState(600, L, bad).heading, false);
    assert.equal(thresholdState(840, L, bad).level, 'near');
  }
  // Already over stays over, and still reports where it is headed.
  const over = thresholdState(900, L, 950);
  assert.equal(over.level, 'over');
  assert.equal(over.heading, true);
});
