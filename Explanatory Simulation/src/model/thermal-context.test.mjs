import test from 'node:test';
import assert from 'node:assert/strict';
import { thermalContext, shouldSwitchMode } from './thermal-context.mjs';
test('nonstudio layer exit unmounts and restores road; returning starts an empty experiment',()=>{
  for(const mode of ['tour','sandbox','trace','viva']) {
    const active=thermalContext(mode,'thermal','thermal',false);
    assert.equal(active.active,true);assert.equal(active.mount,true);
    const exit=thermalContext(mode,'vehicle','thermal',false);
    assert.equal(exit.active,false);assert.equal(exit.mount,false);
    const returned=thermalContext(mode,'thermal','thermal',false);
    assert.equal(returned.mount,true);assert.equal(returned.key,active.key);
    // React removed the keyed instance on exit; a new instance is required on return.
    assert.equal(thermalContext(mode,'thermal','engine',false).mount,false);
  }
});
test('studio explicit entry/return and mode changes control experiment ownership',()=>{
 assert.equal(thermalContext('studio','thermal','system',false).mount,false);
 assert.equal(thermalContext('studio','thermal','system',true).mount,true);
 assert.equal(thermalContext('studio','vehicle','system',true).mount,false);
 assert.notEqual(thermalContext('tour','thermal','thermal',false).key,thermalContext('sandbox','thermal','thermal',false).key);
 assert.equal(thermalContext('studio','thermal','results',true).mount,false);
});

test('repeating active mode retains component and selected source; results can exit explicitly',()=>{
 for(const mode of ['tour','sandbox','trace','viva','studio']) {
  assert.equal(shouldSwitchMode(mode,mode,'thermal'),false);
  assert.equal(shouldSwitchMode(mode,mode,'system'),false);
  assert.equal(shouldSwitchMode(mode,mode,'results'),true);
  assert.equal(shouldSwitchMode(mode,mode==='studio'?'tour':'studio','thermal'),true);
 }
});
