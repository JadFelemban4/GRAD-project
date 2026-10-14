import test from 'node:test';
import assert from 'node:assert/strict';
import { createRecordController, engineOverlay, actuatorComparison } from './record-state.mjs';
const metadata={state:'available',source_revision:'r1',kind:'training',episodes:[{id:0,samples:650,time_unit:'step'}],channels:[]};
test('compact actuator comparison preserves command and physical units and missing values',()=>{
  const rows=actuatorComparison({values:{command:-.5,applied:2}},[
    {id:'command',actuator:'spark',group:'command_trim',unit:'normalized [-1,1]',state:'recorded'},
    {id:'applied',actuator:'spark',group:'applied_trim',unit:'deg',state:'recorded'}]);
  assert.equal(rows.length,5);
  assert.deepEqual(rows[0],{actuator:'spark',command:{value:-.5,unit:'normalized [-1,1]'},applied:{value:2,unit:'deg'}});
  assert.deepEqual(rows[1].applied,{value:null,unit:null});
});
test('record windows stay bounded and seeking retains original sample identity',async()=>{
  const calls=[];
  const model=createRecordController({readMeta:async()=>metadata,readWindow:async(_id,episode,start,count)=>{
    calls.push({episode,start,count});return {source_revision:'r1',frames:Array.from({length:Math.min(count,650-start)},(_,i)=>({sample_index:start+i,time:null,values:{}}))};
  }});
  await model.select('record',0);await model.seek(599);
  assert.deepEqual(calls,[{episode:0,start:0,count:200},{episode:0,start:400,count:200}]);
  assert.equal(model.get().frame.sample_index,599);assert.equal(model.get().frame.time,null);
  assert.equal(model.get().selection.get().sampleIndex,599);
  await model.step(1);assert.equal(model.get().frame.sample_index,600);
  assert.equal(calls.at(-1).count,50);model.dispose();
});
test('old metadata arriving after a new source cannot replace its selected record',async()=>{
  let old;const model=createRecordController({readMeta:id=>id==='old'?new Promise(r=>old=r):Promise.resolve(metadata),
    readWindow:async()=>({source_revision:'r1',frames:[{sample_index:0,time:0,values:{}}]})});
  const pending=model.select('old');await model.select('new');old({...metadata,source_revision:'obsolete'});await pending;
  assert.equal(model.get().id,'new');assert.equal(model.get().meta.source_revision,'r1');model.dispose();
});
test('replaced recording invalidates the visible sample instead of mixing generations',async()=>{
  const model=createRecordController({readMeta:async()=>metadata,
    readWindow:async()=>({source_revision:'r2',frames:[{sample_index:0,time:0,values:{}}]})});
  await model.select('record');assert.equal(model.get().frame,null);
  assert.equal(model.get().reason,'source_changed');assert.equal(model.get().selection.get().sampleIndex,null);model.dispose();
});
test('playback waits for bounded reads and crosses two window boundaries',async(t)=>{
  t.mock.timers.enable({apis:['setTimeout']});
  const calls=[];let release;
  const makeWindow=(start,count)=>({source_revision:'r1',frames:Array.from({length:count},(_,i)=>({sample_index:start+i,time:null,values:{}}))});
  const model=createRecordController({readMeta:async()=>metadata,readWindow:(_id,_episode,start,count)=>{
    calls.push({start,count});
    return start===0?Promise.resolve(makeWindow(start,count)):new Promise(resolve=>{release=()=>resolve(makeWindow(start,count));});
  }});
  await model.select('record');await model.seek(199);model.play();
  t.mock.timers.tick(150);
  assert.equal(model.get().loading,true);assert.equal(model.get().playing,true);
  release();await new Promise(resolve=>setImmediate(resolve));
  assert.equal(model.get().frame.sample_index,200);assert.equal(model.get().playing,true);
  assert.equal(model.get().selection.get().sampleIndex,200);
  await model.seek(399);t.mock.timers.tick(150);
  assert.equal(model.get().loading,true);assert.equal(model.get().playing,true);
  release();await new Promise(resolve=>setImmediate(resolve));
  assert.equal(model.get().frame.sample_index,400);assert.equal(model.get().playing,true);
  assert.deepEqual(calls,[{start:0,count:200},{start:200,count:200},{start:400,count:200}]);
  model.pause();assert.equal(model.get().playing,false);model.dispose();
});
test('engine overlays convert only recorded temperature units and retain unavailable channels',()=>{
  const channels=[{id:'engine.t_turb',unit:'K'},{id:'engine.t_oil',unit:'C'}];
  assert.deepEqual(engineOverlay({time:2,values:{'engine.t_turb':573.15,'engine.t_oil':90}},channels),
    {turbine_c:300,oil_c:90,block_c:null,coolant_c:null,time:2});
  assert.equal(engineOverlay({time:null,values:{'engine.t_turb':999}},[{id:'engine.t_turb',unit:'unknown'}]).turbine_c,null);
});
