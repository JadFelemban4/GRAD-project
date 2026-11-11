import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { GROUPS, GROUP_OF, buildGraph, causesOf, effectsOf, layout, radiusOf, searchNodes } from './concept-map.mjs';

const read = (file) => JSON.parse(readFileSync(new URL('../../' + file, import.meta.url), 'utf8'));
const en = read('content.json'), ar = read('content.ar.json');

test('every concept has a group, and every group is a real one', () => {
  const groups = new Set(GROUPS.map(g => g.id));
  for (const c of en.concepts) assert.ok(groups.has(GROUP_OF[c.id]), `no group for ${c.id}`);
  assert.deepEqual(Object.keys(GROUP_OF).sort(), en.concepts.map(c => c.id).sort());
});

test('both languages draw the same map', () => {
  const key = (g) => g.edges.map(e => e.from + '>' + e.to).sort();
  assert.deepEqual(key(buildGraph(ar.concepts)), key(buildGraph(en.concepts)));
});

test('every link comes from the content files, counted once, cause to effect', () => {
  const graph = buildGraph(en.concepts);
  const written = new Set();
  for (const c of en.concepts) {
    for (const u of c.upstream || []) written.add(u + '>' + c.id);
    for (const d of c.downstream || []) written.add(c.id + '>' + d);
  }
  assert.deepEqual(graph.edges.map(e => e.from + '>' + e.to).sort(), [...written].sort());
  assert.ok(causesOf(graph, 'charge_temp').includes('ambient_temp'));
  assert.ok(effectsOf(graph, 'charge_temp').includes('knock'));
});

test('the layout is the same every time, inside the frame, and no two circles touch', () => {
  const graph = buildGraph(en.concepts);
  const a = layout(graph), b = layout(graph);
  assert.deepEqual(a, b);
  for (const n of graph.nodes) {
    const p = a[n.id];
    assert.ok(Number.isFinite(p.x) && Number.isFinite(p.y) && p.x >= 0 && p.x <= 1000 && p.y >= 0 && p.y <= 640, n.id);
  }
  for (let i = 0; i < graph.nodes.length; i++) for (let j = i + 1; j < graph.nodes.length; j++) {
    const [p, q] = [a[graph.nodes[i].id], a[graph.nodes[j].id]];
    assert.ok(Math.hypot(p.x - q.x, p.y - q.y) > radiusOf(graph.nodes[i]) + radiusOf(graph.nodes[j]), `${graph.nodes[i].id} touches ${graph.nodes[j].id}`);
  }
});

test('search finds a concept by its name in either language and by its id', () => {
  assert.equal(searchNodes(buildGraph(en.concepts), 'turbine')[0].id, 't_turb');
  assert.ok(searchNodes(buildGraph(ar.concepts), 'التوربين').some(n => n.id === 't_turb'));
  assert.equal(searchNodes(buildGraph(en.concepts), 'h_over')[0].id, 'h_over_tau');
  assert.deepEqual(searchNodes(buildGraph(en.concepts), '   '), []);
});
