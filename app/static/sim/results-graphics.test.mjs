import test from 'node:test';
import assert from 'node:assert/strict';
import { panelView, numericDomain, exactRows, createGraphicsPanel } from './results-graphics.mjs?v=R1a';
import { installFakeDocument, fakeHost, walk } from './charts-fake-dom.mjs';
import { createMounter } from './charts-lib.mjs?v=R1a';
import { createChartSelection } from './chart-selection.mjs?v=R1a';
const panel = { id:'G08', state:'available', kind:'line', source_files:['set/a.json'], revision:'one',
  axes:{x:{label:'seed',unit:''},y:{label:'damage',unit:'absolute'}},
  series:[{id:'sighted',label:'sighted',points:[{x:0,y:2,seed:0,source_index:0},{x:1,y:5,seed:1,source_index:1}]},
    {id:'blind',label:'blind',points:[{x:0,y:3,seed:0,source_index:0},{x:1,y:null,seed:1,source_index:1}]}],
  channels:[{id:'thermal',label:'thermal_damage',unit:'absolute',series:[{id:'sighted',label:'sighted',points:[{x:0,y:1}]}]}] };
test('channel and visibility select recorded values without changing source panel', () => {
  assert.equal(panelView(panel, {}).series[0].points[0].y, 2);
  assert.equal(panelView(panel, {channel:'thermal'}).series[0].points[0].y, 1);
  assert.equal(panelView(panel, {hidden:['blind']}).series.length, 1);
  assert.equal(panel.series.length, 2);
});
test('display domains include recorded endpoints and never hide a zero bar baseline', () => {
  assert.deepEqual(numericDomain([2,5,null,Infinity], true), [0,5]);
  assert.deepEqual(numericDomain([]), [0,1]);
  assert.deepEqual(numericDomain([2,2]), [1,3]);
});
test('exact-value rows retain missing values, seed zero and original sample indices', () => {
  const rows = exactRows(panelView(panel, {}));
  assert.deepEqual(rows[0], ['sighted',0,2,null,null,0,0,null,null]);
  assert.equal(rows[3][2], null);
});
test('mounted plot supports keyboard pair selection, tables and teardown', () => {
  installFakeDocument();
  const parent = fakeHost(800);
  const store = createChartSelection({sourceRevision:'one',axisKind:'pair'});
  const mounts = createMounter();
  const view = createGraphicsPanel({...panel,channels:[]}, {lang:'en',mounter:mounts,selection:store});
  parent.appendChild(view.node);
  const chart = walk(view.node).find(n => n.attrs.class === 'rc-chart rg-plot');
  chart.clientWidth=720; view.mount();
  assert.ok(walk(chart).some(n=>n.tagName==='svg'));
  chart.dispatch('keydown',{key:'ArrowRight',preventDefault(){}});
  assert.equal(store.get().pairSeed,1);
  assert.ok(walk(view.node).some(n=>n.tagName==='details'));
  const prior = store.get(); view.unmount();
  store.reset(); assert.equal(prior.pairSeed,1);
  mounts.dispose();
});
