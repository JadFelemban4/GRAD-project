import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import ts from 'typescript';
import React from 'react';
import { renderToStaticMarkup } from 'react-dom/server';
import { uiText } from './ui-copy.mjs';
import { thermalContext } from './thermal-context.mjs';

// Execute the actual App handlers, including their setter wiring, without WebGL.
const app = readFileSync(new URL(process.env.THERMAL_APP_SOURCE || '../App.tsx', import.meta.url), 'utf8');
const tree = ts.createSourceFile('App.tsx', app, ts.ScriptTarget.Latest, true, ts.ScriptKind.TSX);
const nodes = [];
function visit(node) { nodes.push(node); ts.forEachChild(node, visit); }
visit(tree);
const declaration = name => nodes.find(n => ts.isVariableDeclaration(n) && n.name.getText(tree) === name);
const layerHandler = nodes.find(n => ts.isFunctionDeclaration(n) && n.name?.text === 'changeLayer');
const answerHandler = nodes.find(n => ts.isArrowFunction(n) && n.body.getText(tree).includes('setAnswer(!answer)'));
const compile = (text, scope) => Function('scope', `with(scope) { ${ts.transpile(`return (${text});`, { target: ts.ScriptTarget.ES2022 })} }`)(scope);
const typeTree = ts.createSourceFile('types.ts', readFileSync(new URL('../types.ts', import.meta.url), 'utf8'), ts.ScriptTarget.Latest, true);
const focusHelper = typeTree.statements.find(n => ts.isFunctionDeclaration(n) && n.name?.text === 'vivaFocus');
const vivaFocus = compile(focusHelper.getText(typeTree).replace(/^export\s+/, ""), {});
const catalog = JSON.parse(readFileSync(new URL('../../content.ar.json', import.meta.url), 'utf8'));
function harness() {
  const result = { time_s: 210, phase: 'cooling', t_block: 355, t_oil: 345, t_turb: 650 };
  const scope = { vivaFocus, mode: 'viva', layer: 'thermal', panel: 'thermal', studioThermal: false, thermalFrame: result, answer: false, readingContext: null, focus: 't_turb', meta: catalog, frames: [{ time_s: 99 }], cursor: 0, labFrame: null, window: {}, session: 'road-session', rightId: 'blind-session', resultsSeed: 7 };
  for (const key of ['layer', 'panel', 'thermalFrame', 'readingContext', 'studioThermal', 'compactInspection', 'running', 'focus', 'answer', 'resultsSeed']) scope[`set${key[0].toUpperCase()}${key.slice(1)}`] = value => { scope[key] = value; };
  const resultsHandler = nodes.find(n => ts.isFunctionDeclaration(n) && n.name?.text === 'openResults');
  if (resultsHandler) scope.openResults = compile(resultsHandler.getText(tree), scope);
  scope.changeLayer = compile(layerHandler.getText(tree), scope);
  const select = compile(declaration('select').initializer.getText(tree), scope);
  const answer = compile(answerHandler.getText(tree), scope);
  function source() {
    scope.thermalActive = thermalContext(scope.mode, scope.layer, scope.panel, scope.studioThermal).active;
    scope.selected = scope.frames[0];
    return compile(`() => ${declaration('frame').initializer.getText(tree)}`, scope)();
  }
  return { scope, result, select, answer, source };
}
for (const entry of ['concept', 'answer']) test(`viva departure and ${entry} reentry discard scene/Inspector result and source time`, () => {
  const h = harness();
  assert.equal(h.source(), h.result);
  h.scope.viva = catalog.viva[0];
  assert.equal(h.scope.viva.layer, 'engine');
  h.answer();
  assert.equal(h.scope.layer, 'engine');
  assert.equal(h.scope.thermalFrame, null);
  assert.equal(thermalContext('viva', h.scope.layer, 'thermal', false).mount, false);
  if (entry === 'concept') h.select('t_oil');
  else { h.scope.viva = catalog.viva[1]; assert.equal(h.scope.viva.layer, 'thermal'); h.answer(); }
  assert.equal(thermalContext('viva', h.scope.layer, 'thermal', false).mount, true);
  assert.equal(h.source(), null);
  assert.equal(h.scope.thermalFrame?.time_s, undefined);
  h.scope.thermalFrame = { ...h.result, time_s: 1 };
  assert.equal(h.source().time_s, 1);
});

function renderedSection(className, scope) {
 const node = nodes.find(n=>ts.isJsxElement(n)&&n.openingElement.attributes.properties.some(a=>ts.isJsxAttribute(a)&&a.name.getText(tree)==='className'&&ts.isStringLiteral(a.initializer)&&a.initializer.text===className));
 assert.ok(node, 'Actual App section '+className);
 return renderedNode(node,scope);
}
function renderedNode(node,scope) {
 const emitted=ts.transpileModule('return ('+node.getText(tree)+');',{compilerOptions:{target:ts.ScriptTarget.ES2022,jsx:ts.JsxEmit.React}}).outputText;
 return Function('React','scope','with(scope) {'+emitted+'}')(React,scope);
}
function elements(root,type) {
 const found=[];
 const walk=node=>{if(!React.isValidElement(node))return;if(node.type===type)found.push(node);React.Children.forEach(node.props.children,walk)};
 walk(root);return found;
}
test('actual bilingual viva seed-results action uses safe Results navigation and retains pair/session',()=>{
 for(const language of ['en','ar']){
  const h=harness(), s=h.scope;
  s.meta=JSON.parse(readFileSync(new URL(language==='en'?'../../content.json':'../../content.ar.json',import.meta.url),'utf8'));
  s.viva=s.meta.viva.at(-1);s.question=s.meta.viva.length-1;s.answer=true;s.running=true;s.studioThermal=true;s.compactInspection=true;s.readingContext={sessionId:s.session};
  s.ui=value=>uiText(value,language);s.t=(ar,en)=>language==='en'?en:ar;s.ArrowRight=()=>null;
  const label=language==='en'?'Open seed results':'افتح نتائج البذور';
  // The route must survive wording changes; identity comes from the catalog destination.
  s.viva={...s.viva,question:'Unrelated question wording'};
  const card=renderedSection('viva-card',s);
  assert.ok(renderToStaticMarkup(card).includes(label),language);
  const button=elements(card,'button').find(node=>renderToStaticMarkup(node).includes(label));
  assert.ok(button,'Rendered Results action '+language);
  s.modeInfo=[];s.Gauge=()=>null;
  const navigation=renderedSection('mode-nav',s);
  const resultsNav=elements(navigation,'button').find(node=>node.props.className.includes('results-nav'));
  assert.equal(button.props.onClick,resultsNav.props.onClick);
  const retained={session:s.session,rightId:s.rightId,frames:s.frames,cursor:s.cursor,resultsSeed:s.resultsSeed};
  button.props.onClick();
  assert.equal(s.panel,'results');assert.equal(s.running,false);assert.equal(s.studioThermal,false);assert.equal(s.thermalFrame,null);assert.equal(s.readingContext,null);assert.equal(s.compactInspection,false);
  for(const [key,value] of Object.entries(retained))assert.equal(s[key],value,key);
  const resultsNode=nodes.find(n=>ts.isJsxSelfClosingElement(n)&&n.tagName.getText(tree)==='Results');s.Results=()=>null;s.setSource=()=>{};
  const results=renderedNode(resultsNode,s);assert.equal(results.props.seed,7);results.props.onSeedChange(3);assert.equal(s.resultsSeed,3);
  s.answer=false;assert.equal(renderToStaticMarkup(renderedSection('viva-card',s)).includes(label),false);s.answer=true;
  s.viva={...s.viva,destination:undefined};assert.equal(renderToStaticMarkup(renderedSection('viva-card',s)).includes(label),false);
 }
});
test('actual comparison lanes retain stable identity across both localized headings',()=>{
 const scope={rightId:'blind-session',session:'sighted-session',selected:{time_s:99},rightFrames:[{time_s:99}],cursor:0,meta:{preview_s:[],concepts:[]},DecisionOutcome:()=>null,buildProjectStory:()=>({}),format:()=>'',valueAt:()=>undefined,setSource:()=>{}};
 const lanes=[];
 for(const language of ['en','ar']){scope.t=(ar,en)=>language==='en'?en:ar;scope.ui=v=>uiText(v,language);const section=renderedSection('compare-lanes',scope);lanes.push(React.Children.toArray(section.props.children));}
 assert.notEqual(lanes[0][0].props.children[0].props.children,lanes[1][0].props.children[0].props.children);
 assert.deepEqual(lanes[0].map(n=>n.key),lanes[1].map(n=>n.key));
 assert.notEqual(lanes[0][0].key,lanes[0][1].key);
 for(const lane of lanes[0]){const outcome=React.Children.toArray(lane.props.children).find(n=>n.type===scope.DecisionOutcome);assert.equal(outcome.props.sessionId,lane===lanes[0][0]?'sighted-session':'blind-session');}
});
test('same-layer thermal concept and viva controls preserve the current result', () => {
  const h = harness();
  for (const id of ['t_oil', 't_block', 't_turb']) { h.select(id); assert.equal(h.source(), h.result); }
  h.scope.viva = catalog.viva[1];
  h.answer(); h.answer();
  assert.equal(h.source(), h.result);
});
test('scene, both Inspectors and source badge consume the tested frame ownership', () => {
  assert.match(app, /<Scene\b[\s\S]*?frame=\{frame\}/);
  const inspectors = [...app.matchAll(/<Inspector\b[\s\S]*?\/>/g)];
  assert.equal(inspectors.length, 2);
  for (const [consumer] of inspectors) { assert.match(consumer, /frame=\{frame\}/); assert.match(consumer, /readingFrame=\{thermalActive\?frame:selected\}/); }
  assert.match(app, /thermalFrame\?<><bdi dir="ltr">\{(?:ui\()?format\(thermalFrame.time_s,1\)\)?\}/);
});

test('actual general viva reveal handles new target lists and preserves explicit layer with valid focus',()=>{
 for(const viva of catalog.viva.filter(v=>Array.isArray(v.focus))){const h=harness();h.scope.viva=viva;h.answer();assert.equal(h.scope.layer,viva.layer || 'agent');assert.equal(typeof h.scope.focus,'string');assert.ok(viva.focus.includes(h.scope.focus));assert.ok(catalog.concepts.some(c=>c.id===h.scope.focus));}
 const h=harness();h.scope.viva={focus:['missing','damage'],layer:'thermal'};h.answer();assert.equal(h.scope.layer,'thermal');assert.equal(h.scope.focus,'damage');assert.equal(h.source(),h.result);
});

