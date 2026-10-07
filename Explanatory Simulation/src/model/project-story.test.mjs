import test from 'node:test';
import assert from 'node:assert/strict';
import { buildProjectStory, PREVIEW_HORIZONS_S } from './project-story.mjs';

test('uses the four preview values aligned to the observation that produced the action', () => {
  const story = buildProjectStory({ input_time_s: 10, time_s: 11, grade_pct: 7, preview_pct: [2, 5, 15, 30], torque_req: 180, egt_c: 810, t_turb: 950, command: [1, 0.02, 4, 0.5, 0.75] }, { preview: true });
  assert.deepEqual(PREVIEW_HORIZONS_S, [2, 5, 15, 30]);
  assert.deepEqual(story.previewSlots.map(slot => slot.gradePct), [2, 5, 15, 30]);
  assert.equal(story.currentGradePct, 7);
});

test('blinding zeros only future preview slots while preserving current grade', () => {
  const story = buildProjectStory({ input_time_s: 10, grade_pct: 8, preview_pct: [3, 5, 9, 12] }, { preview: false });
  assert.deepEqual(story.previewSlots.map(slot => slot.gradePct), [0, 0, 0, 0]);
  assert.equal(story.currentGradePct, 8);
});

test('falls back to source road at input time plus horizons and keeps missing data unavailable', () => {
  const road = { time_s: Array.from({ length: 40 }, (_, i) => i), grade_pct: Array.from({ length: 40 }, (_, i) => i / 2) };
  const story = buildProjectStory({ input_time_s: 3, grade_pct: 0, preview_pct: [NaN] }, { preview: true, road, time: 100 });
  assert.deepEqual(story.previewSlots.map(slot => slot.gradePct), [2.5, 4, 9, 16.5]);
  assert.equal(story.currentGradePct, 0);
  const unavailable = buildProjectStory({ grade_pct: NaN }, { preview: true });
  assert.deepEqual(unavailable.previewSlots.map(slot => slot.gradePct), [null, null, null, null]);
});

test('keeps finite torque, converts finite kelvin to Celsius, and preserves zero action values', () => {
  const story = buildProjectStory({ input_time_s: 0, time_s: 1, torque_req: 0, egt_c: Infinity, t_turb: 573.15, action: [0, 0, 0, 0, 0], command: [0, -0.15, 0, 0, 0.3] }, { preview: true });
  assert.equal(story.torqueReqNm, 0);
  assert.equal(story.egtC, null);
  assert.equal(story.turbineC, 300);
  assert.deepEqual(story.controls.map(item => item.value), [0, -0.15, 0, 0, 0.3]);
});

test('does not present reset-frame placeholder commands as applied actuator values', () => {
  const story = buildProjectStory({ action: null, command: [0, 0, 0, 0, 0] }, { preview: true });
  assert.deepEqual(story.controls.map(item => item.value), [null, null, null, null, null]);
});

test('distinguishes the input sample, interval outputs, and end thermal state', () => {
  const first = buildProjectStory({ input_time_s: 0, time_s: 1, dt: 1, grade_pct: 0, torque_req: 100, egt_c: 700, t_turb: 600, action: [0, 0, 0, 0, 0], command: [0, 0, 0, 1, 1] });
  assert.equal(first.timeline.inputS, 0);
  assert.equal(first.timeline.endS, 1);
  assert.equal(first.timeline.hasAppliedAction, true);
  assert.equal(first.timeline.intervalEgtC, 700);
  assert.equal(first.timeline.endTurbineC, 600 - 273.15);
  const reset = buildProjectStory({ input_time_s: 0, time_s: 0, dt: 1, action: null, command: [0, 0, 0, 0, 0] });
  assert.equal(reset.timeline.hasAppliedAction, false);
  assert.equal(reset.timeline.endS, 0);
  assert.equal(reset.timeline.intervalEgtC, null);
});
