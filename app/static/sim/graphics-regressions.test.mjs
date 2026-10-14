import test from 'node:test';
import assert from 'node:assert/strict';
import { createGraphicsPanel, panelView } from './results-graphics.mjs';
import { createGraphicsBrowser } from './graphics-browser.mjs';
import { createMounter } from './charts-lib.mjs?v=R1a';
import { createChartSelection } from './chart-selection.mjs?v=R1a';
import { graphicsText } from './graphics-strings.mjs?v=R1a';
import { installFakeDocument, fakeHost, walk } from './charts-fake-dom.mjs';

function mounted(panel, axisKind='time') {
  installFakeDocument();
  const store=createChartSelection({sourceRevision:'fixture',axisKind});
  const mounter=createMounter({onError:(_h,e)=>{throw e;}});
  const view=createGraphicsPanel({state:'available',revision:'fixture',source_files:[],...panel},
    {lang:'ar',selection:store,mounter});
  const chart=walk(view.node).find(n=>n.classes().includes('rg-plot'));
  chart.clientWidth=720;view.mount();
  return {view,chart,store,dispose(){view.unmount();mounter.dispose();}};
}
test('legacy evaluation remains a reachable group alongside new training panels',()=>{
  installFakeDocument();const host=fakeHost(720),groups=[];
  const browser=createGraphicsBrowser(host,{onGroup:g=>groups.push(g)});
  browser.render({sourceKey:'exp-d2',lang:'en',title:'D2',externalGroups:{evaluation:2},
    panels:[{id:'G13',group:'training',state:'unavailable',revision:'fixture',source_files:[]}]});
  const evaluation=walk(host).find(n=>n.tagName==='button'&&n.textContent==='Evaluation · 2');
  assert.ok(evaluation);assert.equal(evaluation.disabled,false);
  assert.equal(groups.at(-1),'evaluation');
  const training=walk(host).find(n=>n.tagName==='button'&&n.textContent==='Training · 1');
  training.dispatch('click');evaluation.dispatch('click');
  assert.deepEqual(groups,['evaluation','training','evaluation']);browser.dispose();
});
test('horizontal histogram reference uses ratio coordinate rather than count coordinate',()=>{
  const fixture=mounted({id:'G22',kind:'bar',axes:{x:{unit:'ratio'},y:{unit:'samples'}},
    series:[{id:'hist',points:[{x:2,y:10},{x:4,y:1000}]}],references:[{axis:'x',value:4}]});
  const ref=walk(fixture.chart).find(n=>n.tagName==='line'&&n.attrs.style?.includes('stroke-dasharray:4 4'));
  assert.equal(ref.attrs.y1,ref.attrs.y2);assert.notEqual(ref.attrs.x1,ref.attrs.x2);
  // Ratio domain is 1.4..4.6 after bar padding. y(4) = 272 - 258*(2.6/3.2).
  assert.ok(Math.abs(Number(ref.attrs.y1)-62.375)<.001);fixture.dispose();
});
test('a channel with independent axes does not inherit unrelated reference markers',()=>{
  const view=panelView({kind:'bar',series:[],references:[{axis:'x',value:4}],intervals:[{start:1,end:2}],
    channels:[{id:'gear',axes:{x:{unit:'gear'},y:{unit:'ratio'}},series:[]}]},{channel:'gear'});
  assert.deepEqual(view.references,[]);assert.deepEqual(view.intervals,[]);
});
test('adapter start/end interval is shaded at its recorded coordinates',()=>{
  const f=mounted({id:'G01',kind:'line',axes:{x:{unit:'s'},y:{unit:'C'}},
    intervals:[{axis:'x',start:2,end:4}],series:[{id:'temp',points:[{x:0,y:100},{x:10,y:200}]}]});
  const shade=walk(f.chart).find(n=>n.tagName==='rect'&&n.attrs.opacity==='0.1');
  assert.ok(shade);assert.ok(Math.abs(Number(shade.attrs.x)-191.6)<.001);
  assert.ok(Math.abs(Number(shade.attrs.width)-127.6)<.001);f.dispose();
});
test('pointer hit layer selects the actual nonzero paired seed by both coordinates',()=>{
  const f=mounted({id:'G08',kind:'line',axes:{x:{unit:'category'},y:{unit:'damage'}},
    series:[{id:'seed0',points:[{x:0,y:1,seed:0},{x:1,y:2,seed:0}]},
      {id:'seed3',points:[{x:0,y:8,seed:3},{x:1,y:9,seed:3}]}]},'pair');
  const marks=walk(f.chart).filter(n=>n.tagName==='circle'&&n.classes().includes('rc-mark'));
  const target=marks[2],hit=walk(f.chart).find(n=>n.classes().includes('rc-hit'));
  hit.dispatch('pointerdown',{clientX:Number(target.attrs.cx),clientY:Number(target.attrs.cy)});
  assert.equal(f.store.get().pairSeed,3);
  f.store.reset();
  hit.dispatch('pointerdown',{pointerType:'touch',clientX:Number(marks[3].attrs.cx),clientY:Number(marks[3].attrs.cy)});
  assert.equal(f.store.get().pairSeed,3);f.dispose();
});
test('populated table-only panel has readable rows without empty cursor or sample controls',()=>{
  const f=mounted({id:'G25',kind:'table',series:[],table:{columns:['quantity','documented limitation'],
    rows:[['Displacement','SOURCE_STATUS_ONLY_NO_ADDITIONAL_ROW_LIMITATION']]}});
  assert.equal(walk(f.view.node).find(n=>n.classes().includes('rg-cursor')).textContent,'');
  assert.equal(walk(f.view.node).find(n=>n.classes().includes('rg-controls')).hidden,true);
  assert.ok(!f.view.node.textContent.includes('SOURCE_STATUS_ONLY'));
  assert.notEqual(graphicsText('ar','documented limitation'),'documented limitation');f.dispose();
});
test('table-only data is available before entering the chart viewport',()=>{
  installFakeDocument();
  const view=createGraphicsPanel({id:'G25',state:'available',kind:'table',series:[],table:{columns:['quantity'],rows:[['Displacement']]}},
    {lang:'en',mounter:{mount(){},unmount(){}}});
  const nodes=walk(view.node);
  assert.equal(nodes.find(n=>n.classes().includes('rg-plot')).hidden,true);
  assert.equal(nodes.find(n=>n.classes().includes('rg-values')).open,true);
  assert.equal(nodes.filter(n=>n.tagName==='table').length,1);
});
