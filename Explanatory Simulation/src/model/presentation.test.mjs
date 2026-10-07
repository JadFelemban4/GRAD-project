import test from 'node:test';
import assert from 'node:assert/strict';
import {advanceVisualCycle,manualCycle} from './presentation.mjs';
test('paused pedagogical motion keeps its crank position',()=>{
  assert.equal(advanceVisualCycle(.4,.5,3000,1,false),.4);
});
test('a slowed teaching cycle advances by RPM without altering simulation state',()=>{
  const state={rpm:1080,time_s:31,torque:336.2};const before=structuredClone(state);
  assert.ok(Math.abs(advanceVisualCycle(0,.1,state.rpm,1,true)-.05)<1e-12);
  assert.deepEqual(state,before);
});
test('manual scrub spans two crank revolutions and wraps at 720 degrees',()=>{
  assert.equal(manualCycle(180),.25);assert.equal(manualCycle(360),.5);
  assert.equal(manualCycle(720),0);assert.equal(manualCycle(-180),.75);
});
test('returning from a suspended tab cannot jump the mechanical explanation',()=>{
  assert.equal(advanceVisualCycle(0,30,1080,1,true),advanceVisualCycle(0,.1,1080,1,true));
  assert.equal(advanceVisualCycle(.3,.1,NaN,1,true),.3);
});
