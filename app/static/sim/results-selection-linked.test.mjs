import test from 'node:test';
import assert from 'node:assert/strict';
import { agentSet, evaluation, snapshot, startResultsPage, settle } from './results-selection-fixture.mjs';

const cases = [
  { name: 'evaluation', hash: '#exp-d2', firstSections: [], sections: [evaluation('d2')],
    items: [agentSet('art_agents')], primary: 'exp-d2', visible: ['exp-d2'], compare: '' },
  { name: 'comparison with neither evaluation available', hash: '#compare:exp-d2:exp-c4', firstSections: [],
    sections: [evaluation('d2'), evaluation('c4')], items: [agentSet('art_agents')],
    primary: 'exp-d2', visible: ['exp-d2', 'exp-c4'], compare: 'exp-c4' },
  { name: 'comparison with only its first evaluation available', hash: '#compare:exp-d2:exp-c4',
    firstSections: [evaluation('d2')], sections: [evaluation('d2'), evaluation('c4')],
    items: [agentSet('art_agents')], primary: 'exp-d2', visible: ['exp-d2', 'exp-c4'], compare: 'exp-c4' },
  { name: 'registry set', hash: '#set:art_second', firstSections: [], sections: [],
    items: [agentSet('art_agents'), agentSet('art_second')], primary: 'set:art_second',
    visible: ['registry-selection'], compare: '' },
];

for (const entry of cases) {
  test(`an explicit ${entry.name} link waits through an updating snapshot with a ready set`, async t => {
    const page = await startResultsPage(t, entry.hash);
    page.reply(await page.next(), snapshot('initial', {
      updating: true, sections: entry.firstSections, items: [agentSet('art_agents')],
    }));
    await settle();
    assert.equal(location.hash, entry.hash, 'the requested fragment survives incomplete results');
    assert.equal(page.nodes['experiment-select'].value, '', 'fallback is deferred until the link can resolve');
    assert.equal(page.nodes.sections.children.length, 0, 'unrequested results are not displayed while waiting');

    await page.refresh(snapshot('arrived', { sections: entry.sections, items: entry.items }));
    assert.equal(location.hash, entry.hash);
    assert.equal(page.nodes['experiment-select'].value, entry.primary);
    assert.equal(page.nodes['compare-select'].value, entry.compare);
    assert.equal(page.nodes['compare-enabled'].checked, Boolean(entry.compare));
    assert.deepEqual(page.nodes.sections.children.map(node => node.id), entry.visible);
  });
}

test('an absent explicit link falls back only after the results snapshot settles', async t => {
  const page = await startResultsPage(t, '#exp-missing');
  page.reply(await page.next(), snapshot('initial', { updating: true, items: [agentSet('art_agents')] }));
  await settle();
  assert.equal(location.hash, '#exp-missing');
  assert.equal(page.nodes['experiment-select'].value, '');
  await page.refresh(snapshot('settled', { sections: [evaluation('d2')], items: [agentSet('art_agents')] }));
  assert.equal(page.nodes['experiment-select'].value, 'exp-d2');
  assert.equal(location.hash, '#exp-d2');
});

test('an explicit user choice supersedes a link awaiting results', async t => {
  const page = await startResultsPage(t, '#exp-d2');
  page.reply(await page.next(), snapshot('initial', { updating: true, items: [agentSet('art_agents')] }));
  await settle();
  page.nodes['experiment-select'].value = 'set:art_agents';
  page.nodes['experiment-select'].listeners.change();
  assert.equal(location.hash, '#set:art_agents');
  await page.refresh(snapshot('arrived', { sections: [evaluation('d2')], items: [agentSet('art_agents')] }));
  assert.equal(page.nodes['experiment-select'].value, 'set:art_agents');
  assert.equal(location.hash, '#set:art_agents');
  assert.deepEqual(page.nodes.sections.children.map(node => node.id), ['registry-selection']);
});

test('history navigation to a missing evaluation also waits while the snapshot is updating', async t => {
  const page = await startResultsPage(t, '#set:art_agents');
  page.reply(await page.next(), snapshot('initial', { updating: true, items: [agentSet('art_agents')] }));
  await settle();
  assert.equal(page.nodes['experiment-select'].value, 'set:art_agents');
  location.hash = '#exp-d2';
  page.events.popstate();
  assert.equal(location.hash, '#exp-d2');
  assert.equal(page.nodes['experiment-select'].value, '');
  await page.refresh(snapshot('arrived', { sections: [evaluation('d2')], items: [agentSet('art_agents')] }));
  assert.equal(page.nodes['experiment-select'].value, 'exp-d2');
  assert.equal(location.hash, '#exp-d2');
});
