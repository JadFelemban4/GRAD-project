import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {finite,selectedPair,includesZero,readingProvenance,loadComparisonInputs} from './provenance.mjs';
const index=JSON.parse(readFileSync(new URL('../../../results/agents/terrain_dt1/index.json',import.meta.url),'utf8'));
test('seed pair uses actual recorded data and actual torque stats, without mutation',()=>{
 const before=JSON.stringify(index); const selected=selectedPair(index,0);
 assert.equal(selected.delta,index.ablation.pairs[0].sighted-index.ablation.pairs[0].blinded);
 assert.deepEqual(selected.sighted.torque_viol,{median:0.011,q1:0.003,q3:0.016,worst:0.024,best:0});
 assert.equal(selectedPair(index,999),null); assert.equal(JSON.stringify(index),before);
});
test('CI includes zero without treating missing or infinite as evidence',()=>{
 assert.equal(includesZero(index.ablation.ci95),true);
 for(const ci of [null,[null,1],[-1,Infinity],[1,2],[]]) assert.equal(includesZero(ci),false);
 assert.equal(finite(0),0); for(const v of [null,undefined,NaN,Infinity,'0']) assert.equal(finite(v),null);
 assert.equal(selectedPair({ablation:{pairs:[{seed:0,sighted:null,blinded:2}]}},0).delta,null);
});
test('reading source and time stay with pressure input / interval / end; missing frame never invents zero',()=>{
 const c={id:'t_oil',source:{file:'thermal.py',line:8,variable:'t_oil'},unit:'K'};
 assert.equal(readingProvenance(c,null,{time_s:4},null).unit,'°C');
 assert.equal(readingProvenance(c,null,null,null).time,null);
 assert.deepEqual(readingProvenance(c,{phase:'interval',inputS:3,endS:4,unit:'°C',value:97},{time_s:4},null).time,[3,4]);
 assert.equal(readingProvenance(c,{phase:'input',inputS:0,endS:0},null,null).time,null);
 assert.equal(readingProvenance(c,null,{time_s:4},{inputS:3,value:101.3,source:'obs_in[10]'}).time,3);
});
test('historical oil and MAPE source remain linked separately, with accurate caveats',()=>{
 const ui=readFileSync(new URL('../ProvenanceDrawer.tsx',import.meta.url),'utf8');
 const table=readFileSync(new URL('../../../validation_table.md',import.meta.url),'utf8');
 const code=readFileSync(new URL('../../../compare_log.py',import.meta.url),'utf8');
 assert.match(table,/97\.0.*103–111.*outside.*In-sample/); assert.match(ui,/validation_table.md.*line:106/);
 assert.match(ui,/not independent validation/);assert.match(ui,/local criterion not yet documented/);
 assert.match(code,/np\.sum\(meas \* mod\) \/ np\.sum\(mod \* mod\)/);assert.match(ui,/not MSE/);
 assert.match(ui,/NASA-STD-7009B/); assert.match(ui,/not a compliance claim/);
});

test('origin follows actual finite current value rather than scientific badge, with unavailable and reference-only categories',()=>{
 const c={id:'oil',evidence:'MEASURED',unit:'°C',source:{file:'thermal.py',line:1}};
 const zero=readingProvenance(c,null,{time_s:0},null,0);
 assert.equal(zero.origin,'simulated'); assert.equal(zero.value,0);assert.equal(zero.time,0);assert.equal(zero.available,true);
 for(const value of [null,NaN,Infinity]) {
  const p=readingProvenance(c,null,{time_s:5},null,value);assert.equal(p.origin,'unavailable');assert.equal(p.value,null);assert.equal(p.time,null);assert.equal(p.available,false);
 }
 const stats={...c,evidence:'STATISTIC',source:{file:'results/agents/terrain_dt1/index.json',line:4632}};
 const statistic=readingProvenance(stats,null,{time_s:5},null);
 assert.equal(statistic.origin,'recorded-statistic');assert.equal(statistic.time,null);assert.equal(statistic.value,null);
 const assumption=readingProvenance({...c,evidence:'ASSUMED'},null,{time_s:5},null);
 assert.equal(assumption.origin,'assumption');assert.equal(assumption.time,null);
 assert.equal(readingProvenance({...c,evidence:'ASSUMED'},null,{time_s:5},null,97).origin,'simulated');
 assert.equal(readingProvenance(c,null,{time_s:5},{value:101.3,inputS:4,source:'obs_in[10]'}).origin,'derived');
 assert.equal(readingProvenance(c,null,{time_s:5},{value:null,inputS:4,source:'obs_in[10]'}).origin,'unavailable');
});
test('MAPE comparison exposes actual relative-load inputs and model expression, fitted scope remains explicit',()=>{
 assert.equal(loadComparisonInputs.measured,'load_meas');assert.equal(loadComparisonInputs.modeled,'load_model');
 assert.equal(loadComparisonInputs.formula,'100 * eta_v * (1 - f_res) * map_kpa / 100');assert.equal(loadComparisonInputs.fitted,true);
 const compare=readFileSync(new URL('../../../compare_log.py',import.meta.url),'utf8');
 assert.match(compare,/load_pairs.append\(\(load_meas, load_model, iat_k\)\)/);
 assert.match(compare,/load_model = 100.0 \* out\["eta_v"\] \* \(1.0 - out\["f_res"\]\) \* map_kpa \/ 100.0/);
});
