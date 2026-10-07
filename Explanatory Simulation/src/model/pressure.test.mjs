import test from 'node:test';
import assert from 'node:assert/strict';
import { pressureReading, pressurePoints } from './pressure.mjs';
const f={input_time_s:4,time_s:5,obs_in:Array(11).fill(0),map_kpa:160};
test('zero and nonzero normalized scenario pressure invert without defaulting',()=>{assert.equal(pressureReading(f,'road').value,101.3);assert.equal(pressureReading({...f,obs_in:[...Array(10).fill(0),2]},'road').value,117.3)});
test('missing null NaN infinity and absent slot stay unavailable',()=>{for(const v of [null,undefined,NaN,Infinity]) assert.equal(pressureReading({...f,obs_in:[...Array(10).fill(0),v]},'road').value,null);assert.equal(pressureReading(null,'road').value,null)});
test('input time belongs to the observation; do not use end time or end observation',()=>{assert.equal(pressureReading({...f,obs:Array(11).fill(2)},'road').inputS,4);assert.equal(pressureReading({...f,input_time_s:undefined},'road').inputS,null)});
test('thermal and absent road sessions cannot borrow road pressure',()=>{assert.equal(pressureReading(f,'').value,null);assert.equal(pressureReading(f,undefined).inputS,null)});
test('identities separate scenario, unavailable compressor, logged pre-throttle and modeled manifold',()=>{const p=pressurePoints(f,'road');assert.deepEqual(p.map(x=>x.id),['atmosphere','compressor','pre-throttle','manifold']);assert.equal(p[0].value,101.3);assert.equal(p[1].value,null);assert.equal(p[2].value,null);assert.equal(p[3].value,160);assert.equal(p[3].gaugeKpa,58.7);assert.equal(pressurePoints(f,'')[3].value,null);assert.equal(pressurePoints({...f,map_kpa:0},'road')[3].value,0);assert.equal(pressurePoints({...f,map_kpa:NaN},'road')[3].value,null)});
