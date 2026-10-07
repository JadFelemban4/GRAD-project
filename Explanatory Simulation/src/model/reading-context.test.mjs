import test from 'node:test';
import assert from 'node:assert/strict';
import { resolveReading } from './reading-context.mjs';
const frame={input_time_s:180,time_s:181,action:[0,0,0,0,0],command:[0,0,0,0,0],obs_in:Array(18).fill(0).concat(-.425),torque_req:335.5,t_block:365.65};
const previous={time_s:180,t_block:365.25};
const context=(field,phase='input',conceptId='torque_req')=>({conceptId,field,phase,label:'قراءة',unit:'Nm',digits:1,sessionId:'a'});
const resolve=(c,f=frame,p=previous,s='a',id=c.conceptId)=>resolveReading(c,{frame:f,previousFrame:p,sessionId:s,previousSessionId:s,conceptId:id});
test('Inspector resolver distinguishes observed demand and interval demand',()=>{assert.ok(Math.abs(resolve(context('observedTorqueReqNm')).value-115)<1e-9);assert.equal(resolve(context('outputs.torque_req','interval')).value,335.5);});
test('thermal input and end convert Kelvin exactly once',()=>{assert.ok(Math.abs(resolve(context('memory.t_block.beforeC','input','t_block')).value-92.1)<1e-9);assert.equal(resolve(context('memory.t_block.afterC','end','t_block')).value,92.5);});
test('missing reset null NaN stay unavailable; real zero survives',()=>{assert.equal(resolve(context('outputs.torque_req','interval'),{time_s:0}).value,null);for(const torque_req of [null,NaN])assert.equal(resolve(context('outputs.torque_req','interval'),{...frame,torque_req}).value,null);assert.equal(resolve(context('outputs.torque_req','interval'),{...frame,torque_req:0}).value,0);});
test('rejects mismatching session or generic different concept',()=>{assert.equal(resolve(context('observedTorqueReqNm'),frame,previous,'b'),null);assert.equal(resolve(context('observedTorqueReqNm'),frame,previous,'a','damage'),null);});
test('advancing retains phase but resolves current time and reading',()=>{const r=resolve(context('observedTorqueReqNm'),{...frame,input_time_s:181,time_s:182,obs_in:Array(18).fill(0).concat(0)});assert.equal(r.value,200);assert.equal(r.inputS,181);assert.equal(r.endS,182);});
import { readFileSync } from 'node:fs';
test('both Inspector consumers share guarded road or experiment reading props',()=>{
 const app=readFileSync(new URL('../App.tsx',import.meta.url),'utf8');
 const consumers=[...app.matchAll(/<Inspector\b[\s\S]*?\/>/g)].map(match=>match[0]);
 assert.equal(consumers.length,2);
 for(const consumer of consumers){
  assert.match(consumer,/readingContext=\{activeReading\}/);
  assert.match(consumer,/readingFrame=\{thermalActive\?frame:selected\}/);
  assert.match(consumer,/previousFrame=\{thermalActive\?undefined:frames\[Math\.min\(cursor, frames\.length - 1\)-1\]\}/);
  assert.match(consumer,/pressureSessionId=\{!thermalActive && frame===selected \? session : ''\}/);
  assert.match(consumer,/sessionId=\{thermalActive\?'':session\}/);
 }
 assert.match(app,/const activeReading = !thermalActive && readingContext\?\.sessionId === session && readingContext\?\.conceptId === focus/);
 const inspector=readFileSync(new URL('../Inspector.tsx',import.meta.url),'utf8');
 assert.match(inspector,/const value = pressure \? pressure.value : reading \? reading.value : conceptValue/);
 assert.match(inspector,/format\(value,reading\?\.digits/);
});
test('experiment source cannot resolve a road session reading; returning road can',()=>{
 const c=context('memory.t_block.beforeC','input','t_block');
 const experiment={time_s:210,phase:'cooling',t_block:355,rpm:800,mdot_fuel:0};
 assert.equal(resolveReading(c,{frame:experiment,previousFrame:undefined,sessionId:'',previousSessionId:'',conceptId:'t_block'}),null);
 assert.ok(Math.abs(resolve(c).value-92.1)<1e-9);
});
test('previous thermal requires same-session matching input time',()=>{const c=context('memory.t_block.beforeC','input','t_block');assert.equal(resolve(c,frame,{...previous,time_s:179}).value,null);assert.equal(resolveReading(c,{frame,previousFrame:previous,sessionId:'a',previousSessionId:'b',conceptId:'t_block'}).value,null);});
test('applied command preserves units, precision and zero',()=>{const r=resolve({...context('controls.fan_duty','applied','fan_duty'),unit:'fraction',digits:2});assert.equal(r.value,0);assert.equal(r.unit,'fraction');assert.equal(r.digits,2);});
test('observed zero and missing observation are distinct',()=>{assert.equal(resolve(context('observedTorqueReqNm'),{...frame,obs_in:Array(18).fill(0).concat(-1)}).value,0);for(const v of [null,NaN])assert.equal(resolve(context('observedTorqueReqNm'),{...frame,obs_in:Array(18).fill(0).concat(v)}).value,null);});
test('end thermal missing and NaN do not become a converted zero',()=>{for(const t_block of [null,NaN])assert.equal(resolve(context('memory.t_block.afterC','end','t_block'),{...frame,t_block}).value,null);});
