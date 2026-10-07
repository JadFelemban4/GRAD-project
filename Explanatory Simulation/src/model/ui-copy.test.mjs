import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import React from 'react';
import { renderToStaticMarkup } from 'react-dom/server';
import ts from 'typescript';
import { UI_COPY, uiText, templateText } from './ui-copy.mjs';
import { readingLabel } from './reading-label.mjs';
import { resolveReading } from './reading-context.mjs';
import { updatePreferences } from './preferences.mjs';
import { readingProvenance } from './provenance.mjs';
const source=fs.readFileSync(new URL('../types.ts',import.meta.url),'utf8');
const emitted=ts.transpileModule(source,{compilerOptions:{module:ts.ModuleKind.ESNext,target:ts.ScriptTarget.ES2022}}).outputText.replace("'./model/ui-copy.mjs'",JSON.stringify(new URL('./ui-copy.mjs',import.meta.url).href));
const types=await import('data:text/javascript;base64,'+Buffer.from(emitted).toString('base64'));
test('explicit presentation copy covers leaf controls, diagrams, charts, source and scientific caveats',()=>{
 for(const [ar,en] of [['المروحة','Fan'],['محاكاة','Modeled'],['إغلاق المصدر','Close source'],['توقيت الشرارة','Spark timing'],['مؤشر الطرق','Knock proxy'],['حاوية التوربين','Turbine housing']])assert.equal(uiText(ar,'en'),en);
 assert.match(uiText('الضغط المطلق يشمل الضغط الجوي، أما ضغط التعزيز فهو الزيادة فوقه. لامدا أقل من 1 تعني وقودًا أكثر لكل وحدة هواء. تنبؤات الحمل والحرارة المرتفعين والطرق غير متحقق منها.','en'),/unvalidated/);
 assert.equal(uiText(' plant.py:391 · obs_in[10] ','en'),' plant.py:391 · obs_in[10] ');
 assert.equal(uiText(0,'en'),0);assert.equal(uiText(null,'en'),null);
});
test('numeric format localizes absence explicitly while keeping finite and zero scientific values identical',()=>{
 assert.equal(types.format(null,1,'en'),'Unavailable');assert.equal(types.format(Infinity,1,'ar'),'غير متاح');
 for(const v of [0,-0.05,101.3,1200])assert.equal(types.format(v,3,'en'),types.format(v,3,'ar'));
});
test('raw API error retained until rendering responds to a language change',async()=>{
 const old=globalThis.fetch;globalThis.fetch=async()=>({ok:false,status:404,json:async()=>({detail:'source is not allowlisted: private.py'})});
 let raw;try{await types.api('source')}catch(e){raw=e.message}finally{globalThis.fetch=old}
 assert.equal(raw,'source is not allowlisted: private.py');assert.equal(types.humanMessage(raw,'en'),'This source cannot be displayed.');assert.equal(types.humanMessage(raw,'ar'),'لا يسمح بعرض هذا المصدر.');
 assert.match(types.humanWarning('The source plant returned non-finite diagnostics: egt_c','en'),/non-finite/);
});
test('API fetch rejection renders connection recovery in the current language',async()=>{
 const old=globalThis.fetch;
 try{
  for(const message of ['Failed to fetch','NetworkError when attempting to fetch resource.','Load failed']){
   const native=new TypeError(message);globalThis.fetch=async()=>{throw native};
   let error;try{await types.api('meta?locale=en')}catch(e){error=e}
   assert.ok(error instanceof Error);
   assert.equal(error.cause,native);
   const raw=error.message;
   assert.match(types.humanMessage(raw,'en'),/local service/);
   assert.match(types.humanMessage(raw,'ar'),/الخدمة المحلية/);
   assert.match(types.humanMessage(raw,'en'),/simulation/);
   assert.equal(error.message,raw);
  }
 }finally{globalThis.fetch=old}
});
test('API keeps JSON parser failures and HTTP model details distinct from transport recovery',async()=>{
 const old=globalThis.fetch;const parser=new SyntaxError('Unexpected token in JSON');
 try{
  globalThis.fetch=async()=>({ok:true,json:async()=>{throw parser}});
  await assert.rejects(types.api('meta'),e=>e===parser);
  assert.doesNotMatch(types.humanMessage(parser.message,'en'),/local service/);
  globalThis.fetch=async()=>({ok:false,status:503,json:async()=>{throw parser}});
  await assert.rejects(types.api('meta'),e=>/local service/.test(types.humanMessage(e.message,'en'))&&/الخدمة المحلية/.test(types.humanMessage(e.message,'ar')));
  globalThis.fetch=async()=>({ok:false,status:400,json:async()=>({detail:'unknown or expired session'})});
  await assert.rejects(types.api('session/expired'),e=>e.message==='unknown or expired session'&&!/local service/.test(types.humanMessage(e.message,'en')));
  const circular={};circular.self=circular;
  await assert.rejects(types.api('session',circular),e=>e instanceof TypeError&&!/local service/.test(types.humanMessage(e.message,'en')));
 }finally{globalThis.fetch=old}
});
test('open preview selection relabels both directions without changing frame or context',()=>{
 const frame={time_s:1,input_time_s:0,grade_pct:0,preview_pct:[2,3,4,5],action:[0,0,0,1,1],command:[0,0,0,1,1],torque:100,torque_req:101};
 const context={conceptId:'preview_15s',field:'previewSlots.2',phase:'input',label:'ميل الطريق بعد 15 ثانية',sessionId:'run',unit:'%',digits:1};const before=structuredClone({frame,context});
 const options={frame,sessionId:'run',conceptId:'preview_15s'};
 assert.equal(resolveReading(context,options).value,4);assert.equal(readingLabel(context,'en'),'Road grade after 15 seconds');
 assert.equal(readingLabel({...context,label:'Road grade after 15 seconds'},'ar'),'ميل الطريق بعد 15 ثانية');assert.deepEqual({frame,context},before);
});
test('stored thermal/action/outcome labels follow current locale, including English-origin selections',()=>{
 assert.equal(readingLabel({field:'memory.t_block.beforeC',label:'Engine metal at input'},'ar'),'معدن المحرك عند الدخل');
 assert.equal(readingLabel({field:'memory.t_oil.afterC',label:'الزيت عند النهاية'},'en'),'Oil at end');
 assert.equal(readingLabel({field:'chains.boost_trim.final',label:'القيمة النهائية من المصدر'},'en'),'Final value from source');
 assert.equal(readingLabel({field:'torqueErrorNm',label:'Tracking error: delivered − demand'},'ar'),'خطأ التتبع: المتحقق − الطلب');
});
test('templates relabel dynamic names while preserving scientific numbers and units',()=>{
 assert.equal(templateText('أسطوانة {0} · {1} · {2}','Cylinder {0} · {1} · {2}','en',[3,'ضغط','يصعد المكبس ويضغط الشحنة المحبوسة.']),'Cylinder 3 · Compression · Piston rises and compresses trapped charge.');
 assert.equal(templateText('{0}، إدخال رقمي','{0}, numeric input','en',['ضغط المانيفولد']),'Manifold pressure, numeric input');
});
test('preference changes preserve draft, reference, selected pair and session identity',()=>{
 const state={language:'ar',theme:'dark',sessionId:'run',cursor:17,pair:3,draft:[2,.01,5,.4,.5],reference:{time:1,torque:100},stage:4};const clone=structuredClone(state);const next=updatePreferences(updatePreferences(state,{language:'en'}),{theme:'light'});
 for(const key of ['sessionId','cursor','pair','draft','reference','stage'])assert.deepEqual(next[key],state[key]);assert.deepEqual(state,clone);
});
test('recorded-statistic provenance never acquires a live timestamp during presentation',()=>{
 const concept={id:'stat',evidence:'STATISTIC',source:{file:'results/x.json',line:1},unit:'pp'};const p=readingProvenance(concept,null,{time_s:91},null,undefined);
 assert.equal(p.time,null);assert.equal(p.origin,'recorded-statistic');assert.equal(types.format(p.time,1,'en'),'Unavailable');
});
test('catalog and JSX presentation inventory contains no untranslated direct Arabic text',()=>{
 const canonical=s=>s.trim().replace(/\s+/g,' ');for(const file of fs.readdirSync(new URL('../',import.meta.url)).filter(f=>f.endsWith('.tsx')&&f!=='Preferences.tsx')){const src=fs.readFileSync(new URL('../'+file,import.meta.url),'utf8'),ast=ts.createSourceFile(file,src,ts.ScriptTarget.Latest,true,ts.ScriptKind.TSX);
 const walk=n=>{if(ts.isJsxText(n))assert.equal(/[\u0600-\u06ff]/.test(n.text),false,file+': '+n.text);if(ts.isCallExpression(n)&&n.expression.getText(ast)==='ui'&&ts.isStringLiteral(n.arguments[0])&&/[\u0600-\u06ff]/.test(n.arguments[0].text))assert.ok(UI_COPY[canonical(n.arguments[0].text)],file+': '+n.arguments[0].text);ts.forEachChild(n,walk)};walk(ast);}
});

const compiled = new Map();
async function componentModule(name) {
 const url = new URL('../'+name,import.meta.url);
 async function compile(url) {
  if(compiled.has(url.href))return compiled.get(url.href);
  let emitted=ts.transpileModule(fs.readFileSync(url,'utf8'),{compilerOptions:{module:ts.ModuleKind.ESNext,target:ts.ScriptTarget.ES2022,jsx:ts.JsxEmit.ReactJSX}}).outputText;
  const imports=[...emitted.matchAll(/(?:from\s+|import\s+)(['"])([^'"]+)\1/g)];
  for(const match of imports){const spec=match[2];if(spec.endsWith('.css')){emitted=emitted.replace(match[0]+';','');continue;}let href;if(spec.startsWith('.')){let dependency=new URL(spec,url);if(!/\.(mjs|ts|tsx)$/.test(spec))dependency=new URL(spec+(fs.existsSync(new URL(spec+'.tsx',url))?'.tsx':'.ts'),url);href=dependency.href.endsWith('.mjs')?dependency.href:await compile(dependency);}else href=import.meta.resolve(spec);emitted=emitted.replace(match[0],match[0].replace(spec,href));}
  const href='data:text/javascript;base64,'+Buffer.from(emitted).toString('base64');compiled.set(url.href,href);return href;
 }
 return import(await compile(url));
}
test('production leaf React renders English prose and accessibility copy, including an open retained Inspector',async()=>{
 const {PreferencesProvider}=await componentModule('Preferences.tsx');const {Plot,PreviewRoad}=await componentModule('Plots.tsx');const {Inspector,SourceDialog}=await componentModule('Inspector.tsx');const {StudioOperatingControls}=await componentModule('StudioControls.tsx');const {ThermalGuide}=await componentModule('ThermalGuide.tsx');const {FlowGuide}=await componentModule('FlowGuide.tsx');const {default:ActuatorEditor}=await componentModule('ActuatorEditor.tsx');const {default:ProjectStory}=await componentModule('ProjectStory.tsx');
 const old=globalThis.window;globalThis.window={localStorage:{getItem:()=>JSON.stringify({language:'en',theme:'light'})}};
 const frame={time_s:1,input_time_s:0,rpm:2500,map_kpa:100,torque:100,torque_req:101,t_turb:500,t_oil:350,t_block:360,mdot_fuel:2,mdot_air:30,egt_c:600,grade_pct:0,action:[0,0,0,1,1],command:[0,0,0,1,1],obs_in:Array(23).fill(0),obs:Array(23).fill(0),preview_pct:[0,0,1,2]};const road={time_s:[0,1],grade_pct:[0,1],speed_kmh:[100,100]};const concept={id:'t_oil',name:'Oil temperature',meaning:'Model state.',why:'Thermal memory.',source:{file:'thermal.py',line:1},unit:'K',evidence:'MODELLED',upstream:[],downstream:[]};const context={conceptId:'t_oil',field:'memory.t_oil.afterC',phase:'end',label:'الزيت عند النهاية',sessionId:'run',unit:'°C',digits:2};const noop=()=>{};
 const items=[React.createElement(Plot,{frames:[frame],cursor:0}),React.createElement(PreviewRoad,{road,frame,preview:true}),React.createElement(Inspector,{concept,meta:{concepts:[concept]},frame,readingFrame:frame,readingContext:context,sessionId:'run',onSelect:noop,onSource:noop}),React.createElement(SourceDialog,{source:{file:'engine_env.py',line:921},onClose:noop}),React.createElement(StudioOperatingControls,{active:true,onFrame:noop}),React.createElement(ThermalGuide,{frame,focus:'t_turb',onSelect:noop}),React.createElement(FlowGuide,{frame,step:0,onStep:noop}),React.createElement(ActuatorEditor,{actions:[],draft:[0,0,0,1,1],onChange:noop,activePolicy:'baseline',comparison:false,busy:false}),React.createElement(ProjectStory,{frame,previousFrame:null,preview:true,road,time:1,onSelect:noop,busy:false,policyLabel:'سياسة يدوية استباقية',sessionId:'run',resetKey:'run',observations:[],actions:[],draft:[0,0,0,1,1],onDraftChange:noop,activePolicy:'manual',comparison:false})];
 try{for(const item of items){const html=renderToStaticMarkup(React.createElement(PreferencesProvider,null,item));assert.equal(/[\u0600-\u06ff]/.test(html),false,item.type.name+': '+html.match(/.{0,30}[\u0600-\u06ff].{0,70}/)?.[0]);} }finally{globalThis.window=old}
});

test('general viva resolves scalar or list focus to a valid single Inspector target',()=>{
 const concepts=[{id:'agent'},{id:'damage'},{id:'policy_reward'}];
 assert.equal(types.vivaFocus({focus:['agent','policy_reward']},concepts),'agent');
 assert.equal(types.vivaFocus({focus:['damage','agent']},concepts),'damage');
 assert.equal(types.vivaFocus({focus:'policy_reward'},concepts),'policy_reward');
 assert.equal(types.vivaFocus({focus:['missing','damage']},concepts),'damage');
});

// Execute selected JSX from the actual production files: branch tests cover the rendering boundary, not a copy of its strings.
function actualJsx(file,className,scope,contains='') {
 const src=fs.readFileSync(process.env.TASK5_RENDER_SOURCE ? process.env.TASK5_RENDER_SOURCE+'/'+file : new URL('../'+file,import.meta.url),'utf8');const tree=ts.createSourceFile(file,src,ts.ScriptTarget.Latest,true,ts.ScriptKind.TSX);let found;
 const visit=node=>{if(!found&&ts.isJsxElement(node)&&node.openingElement.attributes.properties.some(attr=>ts.isJsxAttribute(attr)&&attr.name.getText(tree)==='className'&&ts.isStringLiteral(attr.initializer)&&attr.initializer.text===className)&&node.getText(tree).includes(contains))found=node;ts.forEachChild(node,visit)};visit(tree);assert.ok(found,'Production JSX '+file+' '+className);
 const emitted=ts.transpileModule('return ('+found.getText(tree)+');',{compilerOptions:{target:ts.ScriptTarget.ES2022,jsx:ts.JsxEmit.React}}).outputText;
 return Function('React','scope','with(scope) { '+emitted+' }')(React,scope);
}
test('actual App not-started and busy JSX translates in English and keeps Arabic and live time',()=>{
 for(const language of ['en','ar']){const scope={ui:value=>uiText(value,language),format:(v,d)=>types.format(v,d,language),thermalFrame:null,busy:true};
  const start=renderToStaticMarkup(actualJsx('App.tsx','thermal-context',scope));const busy=renderToStaticMarkup(actualJsx('App.tsx','subtle',scope,'busy ?'));
  if(language==='en'){assert.match(start,/Source has not run yet; readings unavailable/);assert.match(busy,/Calculating/);assert.equal(/[\u0600-\u06ff]/.test(start+busy),false);}else{assert.match(start,/لم يُشغّل المصدر/);assert.match(busy,/جارٍ الحساب/);}
  scope.thermalFrame={time_s:0,phase:'heating'};scope.thermalPhase=()=>uiText('تسخين',language);const live=renderToStaticMarkup(actualJsx('App.tsx','thermal-context',scope));assert.match(live,/0\.0 s<\/bdi>/);assert.equal(live.includes('Source has not run yet'),false);
 }
});
test('actual Scene ignition cue translates finite zero, advance, retard and unavailable without changing angles',async()=>{
 const {ignitionCommandDegrees}=await import('./engine-cycle.mjs');
 for(const language of ['en','ar'])for(const spark of [0,15,-5,null,NaN]){const scope={ui:value=>uiText(value,language),uiTemplate:(ar,en,...values)=>templateText(ar,en,language,values),sparkCommand:ignitionCommandDegrees(spark),p:{frame:{spark}}};
  const html=renderToStaticMarkup(actualJsx('Scene.tsx','engine-ignition-cue',scope));
  if(language==='en'){assert.equal(/[\u0600-\u06ff]/.test(html),false);if(scope.sparkCommand===null)assert.match(html,/Spark timing unavailable/);else{assert.match(html,new RegExp('Ignition command at '+scope.sparkCommand+'°'));assert.ok(html.includes(spark===0?'At top dead center':spark>0?'15° before top dead center':'5° after top dead center'));}}
  else{assert.match(html,scope.sparkCommand===null?/توقيت الشرارة غير متاح/:/أمر الإشعال عند/);}
 }
});
test('actual missing-value metric and reward JSX retains every value, unit and LTR isolation',()=>{
 const scope={ui:value=>uiText(value,'en'),format:(v,d)=>types.format(v,d,'en'),valueAt:types.valueAt,frame:null,visibleMetrics:['torque','egt_c','t_turb','mdot_fuel'],unitFor:{torque:'Nm',egt_c:'°C',t_turb:'°C',mdot_fuel:'g/s'},select:()=>{}};
 const metrics=renderToStaticMarkup(actualJsx('App.tsx','metric-strip',scope));const rewards=renderToStaticMarkup(actualJsx('App.tsx','reward-terms',scope));assert.equal((metrics.match(/Unavailable/g)||[]).length,4);assert.equal((rewards.match(/Unavailable/g)||[]).length,3);for(const unit of ['Nm','°C','g/s'])assert.ok(metrics.includes(unit));assert.equal((metrics.match(/strong dir="ltr"/g)||[]).length,4);assert.equal((rewards.match(/strong dir="ltr"/g)||[]).length,3);
 const css=fs.readFileSync(process.env.TASK5_RENDER_SOURCE ? process.env.TASK5_RENDER_SOURCE+'/theme.css' : new URL('../theme.css',import.meta.url),'utf8');assert.match(css,/:root \.metric-strip\{grid-template-columns:repeat\(4,minmax\(0,1fr\)\);overflow:visible\}/);assert.match(css,/:root \.metric-strip strong\{[^}]*flex-wrap:wrap[^}]*white-space:normal/);assert.match(css,/@media\(max-width:700px\)\{\s*:root \.metric-strip\{grid-template-columns:repeat\(2,minmax\(0,1fr\)\)\}[\s\S]*:root \.reward-terms\{grid-template-columns:minmax\(0,1fr\)\}/);
});
