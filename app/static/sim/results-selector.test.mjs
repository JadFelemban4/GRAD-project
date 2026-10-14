import test from 'node:test';
import assert from 'node:assert/strict';
import { parseSelectionHash, resolveChoice, selectedSections, selectionHash } from './results-selector.mjs';

const section = (id, state = 'unavailable') => ({ id: `exp-${id}`, prefix: id, state });
const evalChoice = value => ({ id: value.id, type: 'evaluation', section: value });

test('a deep link chooses its experiment, then a retained selection survives arrivals', () => {
  const first = [section('d'), section('d2')].map(evalChoice);
  assert.equal(resolveChoice(first, null, '#exp-d2'), 'exp-d2');
  assert.equal(resolveChoice([...first, evalChoice(section('c4'))], 'exp-d2', ''), 'exp-d2');
});

test('a deleted selection falls back to the first available experiment', () => {
  const available = [section('d'), section('c4')].map(evalChoice);
  assert.equal(resolveChoice(available, 'exp-d2', '#exp-d2'), 'exp-d');
  assert.equal(resolveChoice([], 'exp-d', '#exp-d'), '');
});

test('automatic fallback prefers a readable evaluation before unavailable sections', () => {
  const choices = [evalChoice(section('d')), evalChoice(section('d2', 'ok')), evalChoice(section('c4'))];
  assert.equal(resolveChoice(choices, null, ''), 'exp-d2');
  assert.equal(resolveChoice([choices[0], choices[2]], null, ''), 'exp-d');
});

test('registry sets are independent choices and do not displace the evaluation fallback', () => {
  const choices = [{ id: 'exp-d2', type: 'evaluation' }, { id: 'set:agents-a', type: 'agent_set' }];
  assert.equal(resolveChoice(choices, null, '#exp-d2'), 'exp-d2');
  assert.equal(resolveChoice(choices, 'set:agents-a', ''), 'set:agents-a');
  assert.equal(resolveChoice([choices[1]], 'exp-d2', ''), 'set:agents-a');
});

test('only the explicitly selected second experiment joins the results scope', () => {
  const sections = [section('d'), section('d2'), section('c4')];
  assert.deepEqual(selectedSections(sections, 'exp-d2', ''), [sections[1]]);
  assert.deepEqual(selectedSections(sections, 'exp-d2', 'exp-c4'), [sections[1], sections[2]]);
  assert.deepEqual(selectedSections(sections, 'exp-d2', 'exp-d2'), [sections[1]]);
});

test('selection fragments round trip evaluation comparisons and registry sets safely', () => {
  const choices = [
    { id: 'exp-d2', type: 'evaluation' },
    { id: 'exp-c4', type: 'evaluation' },
    { id: 'set:art_agents-a', type: 'agent_set', item: { id: 'art_agents-a' } },
  ];
  const comparison = selectionHash('exp-d2', 'exp-c4', choices);
  assert.equal(comparison, '#compare:exp-d2:exp-c4');
  assert.deepEqual(parseSelectionHash(comparison, choices), {
    primary: 'exp-d2', compare: 'exp-c4', compareEnabled: true,
  });
  const set = selectionHash('set:art_agents-a', '', choices);
  assert.equal(set, '#set:art_agents-a');
  assert.deepEqual(parseSelectionHash(set, choices), {
    primary: 'set:art_agents-a', compare: '', compareEnabled: false,
  });
  assert.deepEqual(parseSelectionHash('#exp-d2', choices), {
    primary: 'exp-d2', compare: '', compareEnabled: false,
  });
  assert.equal(parseSelectionHash('#set:%E0%A4%A', choices), null);
});
