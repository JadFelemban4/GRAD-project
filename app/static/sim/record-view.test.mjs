import test from 'node:test';
import assert from 'node:assert/strict';
import { FakeEl,walk } from './charts-fake-dom.mjs';
import { createRecordView } from './record-view.mjs';

test('timeline input reads the chosen sample before pause redraws the slider',async()=>{
  class Node extends FakeEl {constructor(tag){super(tag);this.dataset={};this.value='';}}
  globalThis.document=new Node('#document');document.documentElement=new Node('html');
  document.createElement=tag=>new Node(tag);document.createElementNS=(_ns,tag)=>{
    if(tag==='canvas')throw new Error('WebGL unavailable in this DOM fixture');return new Node(tag);
  };
  globalThis.window={matchMedia:()=>({matches:false})};
  const item={id:'record',relative_path:'results/agents/fixture/sighted_seed0',expected_file:'eval_record.npz',
    source_revision:'r1',policy:'sighted_seed0',kind:'evaluation',state:'available',provenance:{}};
  const metadata={...item,episodes:[{id:0,samples:240}],channels:[]};
  const host=new Node('section');
  const view=createRecordView(host,{lang:'en',initialRecord:'record',request:async url=>({status:200,json:async()=>{
    if(url==='/api/records')return {records:[item]};if(url.endsWith('/meta'))return metadata;
    const params=new URL(url,'http://localhost').searchParams,start=Number(params.get('start')),count=Number(params.get('count'));
    return {source_revision:'r1',start,frames:Array.from({length:count},(_,i)=>({sample_index:start+i,time:(start+i)*.25,values:{}}))};
  }})});
  try{
    await view.refresh();assert.equal(view.getSnapshot().frame.sample_index,0);
    const slider=walk(host).find(node=>node.tagName==='input'&&node.attrs.type==='range');
    slider.value='200';slider.dispatch('input');await new Promise(resolve=>setImmediate(resolve));
    assert.equal(view.getSnapshot().frame.sample_index,200);
    assert.equal(view.getSnapshot().frame.time,50);
    assert.equal(slider.value,'200');
  }finally{view.dispose();}
});
