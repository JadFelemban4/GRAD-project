import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { STRINGS, LANGS, missingKeys } from './i18n.mjs';
import { ARTIFACT_STRINGS, mergeArtifactStrings } from './artifact-strings.mjs';
import { itemView, statusView } from './artifact-view.mjs';

const item = over => ({
  id: 'run-x', relative_path: 'runs/phase/sighted_seed0', kind: 'run_pair', revision: 'rev1',
  lifecycle: 'running', compatibility: { replay_allowed: false, reason: 'different plant' },
  capabilities: { model: true, training_curve: true, training_record: false, evaluation_summary: false, evaluation_record: false, verdict: false },
  source_files: ['runs/phase/sighted_seed0/config.json'], issues: ['config is still changing'], arms: [], pairs: [], ...over,
});

test('itemView names source, lifecycle, evidence, compatibility, and raw issue/refusal reasons', () => {
  const view = itemView(item(), 'en');
  assert.match(view.source, /runs\/phase\/sighted_seed0/);
  assert.match(view.lifecycle, /running/i);
  assert.match(view.availability, /model/i);
  assert.match(view.availability, /training record/i);
  assert.match(view.compatibility, /different plant/);
  assert.match(view.issues, /config is still changing/);
});

test('missing evidence is explicitly unavailable and unknown lifecycle stays explicit', () => {
  const view = itemView(item({ lifecycle: 'mystery', capabilities: {} }), 'en');
  assert.match(view.lifecycle, /unknown/i);
  assert.match(view.availability, /model.*unavailable/i);
  assert.match(view.availability, /evaluation summary.*unavailable/i);
});

test('evaluation text results remain available as summaries and agent sets await their reader', () => {
  const resultOnly = item({ kind: 'evaluation_text', lifecycle: 'finished',
    compatibility: { replay_allowed: false, reason: null }, capabilities: { evaluation_summary: true } });
  const result = itemView(resultOnly, 'en');
  assert.match(result.availability, /evaluation summary.*available/i);
  assert.match(result.lifecycle, /published/i);
  assert.doesNotMatch(result.lifecycle, /training finished/i);
  assert.doesNotMatch(result.availability, /awaiting reader/i);
  assert.match(result.compatibility, /unknown/i);
  assert.match(itemView(resultOnly, 'ar').compatibility, /غير معروف/);
  const set = itemView(item({ kind: 'agent_set', capabilities: { evaluation_summary: true } }), 'en');
  assert.match(set.availability, /awaiting reader/i);
});

test('statusView exposes connection state, last successful update and restart warning', () => {
  const view = statusView({ revision: 'x', updating: true, last_success_at: '2026-10-07T10:00:00Z', restart_needed: true }, 'en');
  assert.match(view.connection, /updating/i);
  assert.match(view.lastSuccess, /2026-10-07T10:00:00Z/);
  assert.ok(view.lastSuccess.includes('\u20662026-10-07T10:00:00Z\u2069'));
  assert.match(view.restartNeeded, /restart/i);
  assert.match(statusView({ updating: false, restart_needed: false }, 'en').connection, /connected/i);
  assert.match(statusView(null, 'en').connection, /offline/i);
});

test('statusView accepts callback status objects and preserves the last success while offline', () => {
  const view = statusView({ state: 'offline', lastSuccessAt: '2026-10-07T10:00:00Z', restart_needed: true }, 'en');
  assert.match(view.connection, /offline/i);
  assert.match(view.lastSuccess, /2026-10-07T10:00:00Z/);
  assert.match(view.restartNeeded, /restart/i);
});

test('artifact strings merge bilingually without collisions and retain shared i18n parity', () => {
  assert.deepEqual(Object.keys(ARTIFACT_STRINGS).sort(), [...LANGS].sort());
  const target = { ar: { base: 'أ' }, en: { base: 'A' } };
  const copy = structuredClone(target);
  assert.throws(() => mergeArtifactStrings(target, { ar: { key: 'نص' }, en: {} }), /missing from en/);
  assert.deepEqual(target, copy);
  assert.throws(() => mergeArtifactStrings(target, { ar: { base: 'تغيير' }, en: { base: 'change' } }), /collides/);
  assert.equal(mergeArtifactStrings(target, { ar: { 'artifact.test': 'نص' }, en: { 'artifact.test': 'Text' } }), 1);
  assert.deepEqual(missingKeys(), []);
  for (const lang of LANGS) for (const [key, text] of Object.entries(ARTIFACT_STRINGS[lang])) assert.equal(STRINGS[lang][key], text);
});

test('all bilingual strings use the same interpolation slots and declare exactly the same keys', () => {
  assert.deepEqual(Object.keys(ARTIFACT_STRINGS.ar).sort(), Object.keys(ARTIFACT_STRINGS.en).sort());
  const slots = text => [...text.matchAll(/\{(\w+)\}/g)].map(match => match[1]).sort();
  for (const key of Object.keys(ARTIFACT_STRINGS.ar)) assert.deepEqual(slots(ARTIFACT_STRINGS.ar[key]), slots(ARTIFACT_STRINGS.en[key]), key);
  const viewSource = readFileSync(new URL('./artifact-view.mjs', import.meta.url), 'utf8');
  assert.match(viewSource, /export function itemView/);
  assert.match(viewSource, /export function statusView/);
});
