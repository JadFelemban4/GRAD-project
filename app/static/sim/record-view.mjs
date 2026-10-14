import { H,createMounter } from './charts-lib.mjs?v=R1a';
import { createGraphicsPanel } from './results-graphics.mjs?v=R1a';
import { createRecordController,engineOverlay,actuatorComparison } from './record-state.mjs';
import { recordText } from './record-strings.mjs';

const ACTUATORS=['spark','lambda','boost','fan','pump'];
const sourceOf=item=>item.relative_path.startsWith('results/agents/')?item.relative_path.split('/').slice(0,3).join('/'):item.relative_path.split('/')[0];
const valueText=value=>Number.isFinite(value)?String(value):'—';
export function createRecordView(host,{lang='ar',request=fetch,initialRecord=null,initialSource=null}={}) {
  let records=[],picked=null,group=initialSource || '',scene=null,disposed=false,active=true,listAbort=null;
  let charts=[],chartKey='',selectionStop=null,selectedCamera='overview',snapshot=null;
  const views=new Map(),tr=key=>recordText(lang,key);
  const mounter=createMounter({onError:(chart,error)=>{H('p',{class:'rc-note',text:`${tr('error')}: ${error.message}`},chart);}});
  const motion=window.matchMedia?.('(prefers-reduced-motion: reduce)');
  const heading=H('h2',{},host),intro=H('p',{class:'record-note'},host);
  const counts=H('p',{class:'record-note',role:'status'},host);
  const controls=H('div',{class:'record-selectors'},host);
  function selectControl(key){const label=H('label',{},controls),title=H('span',{},label);
    const select=H('select',{'aria-label':tr(key)},label);return {title,select,key};}
  const source=selectControl('source'),record=selectControl('record'),episode=selectControl('episode');
  const identity=H('div',{class:'record-identity',role:'status','aria-live':'polite'},host);
  const path=H('p',{dir:'ltr'},identity),generation=H('p',{},identity),status=H('p',{},identity);
  const scope=H('p',{class:'record-note'},host),phase=H('p',{class:'record-note'},host);
  const transport=H('div',{class:'record-transport'},host);
  const previous=H('button',{type:'button'},transport),play=H('button',{type:'button'},transport),next=H('button',{type:'button'},transport);
  const seek=H('input',{type:'range',min:0,max:0,step:1,value:0},transport);
  const sample=H('p',{class:'record-sample',role:'status'},host),windowNote=H('p',{class:'record-note'},host);
  const mechanical=H('section',{class:'record-mechanical'},host),mechanicalTitle=H('h3',{},mechanical);
  const cameras=H('div',{class:'record-camera'},mechanical);
  const cameraButtons=['overview','turbo','intake','cooling'].map(key=>{
    const button=H('button',{type:'button','aria-pressed':String(key===selectedCamera)},cameras);
    button.addEventListener('click',()=>{selectedCamera=key;scene?.setCamera(key);renderCamera();});return {button,key};});
  const engineHost=H('div',{class:'record-engine',role:'img'},mechanical);
  const schematic=H('p',{class:'record-note'},mechanical),reduced=H('p',{class:'record-note'},mechanical);
  const fallback=H('p',{class:'record-note',hidden:true},mechanical);
  const diagram=H('div',{class:'record-paths'},mechanical);
  const paths=['air_in','gas_out','cooling_flow'].map(key=>({key,node:H('p',{class:`record-path ${key}`,dir:'ltr'},diagram)}));
  const temperatures=H('dl',{class:'record-temperatures'},mechanical),tempNodes={};
  for(const key of ['turbine_c','oil_c','block_c','coolant_c']){
    const cell=H('div',{},temperatures);tempNodes[key]={label:H('dt',{},cell),value:H('dd',{dir:'ltr',text:'—'},cell)};}
  const actionMode=H('div',{class:'record-action-mode'},host);
  const modeButtons=['command','applied'].map(key=>{
    const button=H('button',{type:'button','aria-pressed':String(key==='command')},actionMode);
    button.addEventListener('click',()=>{host.dataset.actionMode=key;for(const b of modeButtons)b.button.setAttribute('aria-pressed',String(b.key===key));});return {button,key};});
  host.dataset.actionMode='command';
  const actionValues=H('div',{class:'record-action-values rg-table-wrap'},host);
  const graphHost=H('div',{class:'record-graphs'},host);
  const details=H('details',{class:'record-values'},host),summary=H('summary',{},details),valuesHost=H('div',{class:'rg-table-wrap'},details);
  const model=createRecordController({
    readMeta:(id,options)=>{
      const item=records.find(item=>item.id===id);
      return item&&item.state!=='available'?Promise.resolve({...item,episodes:[],channels:[]}):json(`/api/records/${encodeURIComponent(id)}/meta`,options);
    },
    readWindow:(id,ep,start,count,options)=>json(`/api/records/${encodeURIComponent(id)}/frames?episode=${ep}&start=${start}&count=${count}`,options),
    onChange:state=>{snapshot=state;render();},
  });
  async function json(url,options={}){const response=await request(url,{cache:'no-store',...options});
    if(response.status!==200)throw new Error(`HTTP ${response.status}`);return response.json();}
  function options(node,entries,value){node.textContent='';H('option',{value:'',text:tr('choose')},node);
    for(const entry of entries)H('option',{value:String(entry.value),text:entry.label},node);node.value=value ?? '';}
  function renderSelectors(){
    for(const control of [source,record,episode]){control.title.textContent=tr(control.key);control.select.setAttribute('aria-label',tr(control.key));}
    options(source.select,[...new Set(records.map(sourceOf))].map(value=>({value,label:value})),group);
    const entries=records.filter(item=>sourceOf(item)===group);
    options(record.select,entries.map(item=>({value:item.id,label:`${item.policy} · ${tr(item.kind)}${item.state==='available'?'':' · '+tr('missing_channel')}`})),picked);
    const state=model.get();
    options(episode.select,(state.meta?.episodes || []).map(ep=>({value:ep.id,label:`${ep.id} · ${ep.samples} ${tr('sample')}`})),state.meta?state.episode:'');
    record.select.disabled=!group;episode.select.disabled=!state.meta?.episodes?.length;
  }
  function renderCamera(){for(const {key,button} of cameraButtons){button.textContent=tr(key);button.setAttribute('aria-pressed',String(key===selectedCamera));}}
  function clearCharts(){for(const view of charts)view.unmount();charts=[];graphHost.textContent='';selectionStop?.();selectionStop=null;chartKey='';}
  function panelFor(channel,frames,state){return {
    id:`G11:${channel.id}`,title:tr(channel.label),description:`${tr(channel.evidence)} · ${tr(channel.phase || 'unknown')}`,
    kind:'line',state:channel.state==='recorded'?'available':'unavailable',reason:channel.state==='recorded'?null:'missing_record',
    source_files:[`${state.meta.relative_path}/${state.meta.kind==='training'?'train_record.npz':'eval_record.npz'}`],
    revision:state.meta.source_revision,axes:{x:{label:frames[0]?.time!=null?'time':'sample',unit:frames[0]?.time!=null?'s':'index'},y:{label:tr(channel.label),unit:tr(channel.unit)}},
    series:channel.state==='recorded'?[{id:channel.id,label:tr(channel.label),points:frames.map(frame=>({x:frame.time ?? frame.sample_index,y:frame.values[channel.id],source_index:frame.sample_index}))}]:[],
  };}
  function renderCharts(state){
    const key=state.window?`${state.meta.source_revision}:${state.episode}:${state.window.start}:${lang}`:'';
    if(key===chartKey)return;clearCharts();if(!state.window||!state.selection)return;chartKey=key;
    const frames=state.window.frames,channels=state.meta.channels;
    const add=(channel,parent)=>{
      const panel=panelFor(channel,frames,state),viewState=views.get(channel.id) || {};views.set(channel.id,viewState);
      const view=createGraphicsPanel(panel,{lang,mounter,selection:state.selection,viewState,plotHeight:190});
      parent.appendChild(view.node);charts.push(view);view.mount();
    };
    for(const actuator of ACTUATORS){
      const row=H('section',{class:'record-actuator-row','data-actuator':actuator},graphHost);
      for(const kind of ['command_trim','applied_trim']){
        const cell=H('div',{class:`record-actuator ${kind}`},row);
        const channel=channels.find(c=>c.actuator===actuator&&c.group===kind);if(channel)add(channel,cell);
      }
    }
    for(const groupName of ['observation','preview','reward','engine','thermal','events']){
      const entries=channels.filter(c=>(c.group===groupName||(groupName==='events'&&c.group==='event'))&&!c.actuator);if(!entries.length)continue;
      const groupHost=H('section',{class:'record-secondary'},graphHost);
      H('h3',{text:tr(groupName)},groupHost);
      const first=entries.find(c=>c.state==='recorded') || entries[0];
      const panel=panelFor(first,frames,state);panel.id=`G11:${groupName}`;panel.title=tr(groupName);
      panel.channels=entries.filter(c=>c.state==='recorded').map(c=>({...panelFor(c,frames,state),id:c.id,label:tr(c.label),unit:tr(c.unit)}));
      const viewState=views.get(groupName) || {};views.set(groupName,viewState);
      const view=createGraphicsPanel(panel,{lang,mounter,selection:state.selection,viewState,plotHeight:220});
      groupHost.appendChild(view.node);charts.push(view);view.mount();
    }
    selectionStop=state.selection.subscribe(cursor=>{
      if(cursor.sampleIndex!=null&&cursor.sampleIndex!==model.get().frame?.sample_index)model.seek(cursor.sampleIndex);
    });
  }
  function renderValues(state){valuesHost.textContent='';if(!state.frame)return;
    const table=H('table',{class:'rc-table'},valuesHost),head=H('tr',{},H('thead',{},table)),body=H('tbody',{},table);
    for(const key of ['channel','value','unit','phase_col','evidence'])H('th',{scope:'col',text:tr(key)},head);
    for(const channel of state.meta.channels){const row=H('tr',{},body);
      for(const value of [tr(channel.label),valueText(state.frame.values[channel.id]),tr(channel.unit),tr(channel.phase || 'unknown'),channel.state==='recorded'?tr(channel.evidence):tr('missing_channel')])H('td',{text:value},row);}
  }
  function renderActions(state){
    actionValues.hidden=!state.frame;actionValues.textContent='';if(!state.frame)return;
    const table=H('table',{class:'rc-table'},actionValues),head=H('tr',{},H('thead',{},table)),body=H('tbody',{},table);
    for(const key of ['actuator','command','unit','applied','unit'])H('th',{scope:'col',text:tr(key)},head);
    const names={spark:'spark_trim',lambda:'lambda_trim',boost:'boost_trim',fan:'fan_duty',pump:'pump_duty'};
    for(const row of actuatorComparison(state.frame,state.meta.channels)){
      const element=H('tr',{'data-actuator':row.actuator},body);
      for(const value of [tr(names[row.actuator]),valueText(row.command.value),tr(row.command.unit),valueText(row.applied.value),tr(row.applied.unit)])H('td',{text:value},element);
    }
  }
  function render(){
    if(disposed)return;const state=model.get(),item=records.find(item=>item.id===picked);
    heading.textContent=tr('heading');intro.textContent=tr('intro');scope.textContent=tr('scope');phase.textContent=tr('phase');
    counts.textContent=`${tr('available')}: ${records.filter(r=>r.state==='available').length} / ${records.length} ${tr('expected')}`;
    path.textContent=item?`${item.relative_path}/${item.expected_file}`:'';
    generation.textContent=item?`${tr('provenance')}: ${state.meta?.source_revision || item.source_revision || '—'} · ${item.provenance?.generation || tr('unknown')} · ${item.protocol || '—'}`:'';
    status.textContent=state.loading?tr('loading'):state.reason?`${tr(state.reason)}${state.reason.startsWith('HTTP')?' · '+tr('error'):''}`:item?.state!=='available'&&item?tr('missing'):picked?'':tr('choose');
    transport.hidden=!state.meta?.episodes?.length;
    actionMode.hidden=!state.window;details.hidden=!state.frame;
    previous.textContent=tr('previous');next.textContent=tr('next');play.textContent=tr(state.playing?'pause':'play');
    for(const button of [previous,next,play])button.disabled=!state.frame||state.loading;
    seek.setAttribute('aria-label',tr('seek'));seek.max=String(Math.max(0,(state.meta?.episodes.find(e=>e.id===state.episode)?.samples || 0)-1));seek.disabled=!state.meta || state.loading;
    seek.value=String(state.frame?.sample_index || 0);
    sample.textContent=state.frame?`${tr('sample')}: ${state.frame.sample_index} · ${tr('episode')}: ${state.episode} · ${tr('time')}: ${state.frame.time==null?'—':state.frame.time+' s'}`:tr('choose');
    windowNote.textContent=state.window?`${tr('window')}: ${state.window.start}–${state.window.frames.at(-1)?.sample_index} / ${seek.max}${state.frame?.time==null?' · '+tr('step_axis'):''}`:'';
    mechanicalTitle.textContent=tr('mechanical');engineHost.setAttribute('aria-label',tr('mechanical'));schematic.textContent=tr('schematic');
    reduced.hidden=!motion?.matches;reduced.textContent=tr('reduced');fallback.textContent=tr('fallback');renderCamera();
    for(const entry of paths)entry.node.textContent=tr(entry.key);
    const overlay=engineOverlay(state.frame,state.meta?.channels);scene?.update(overlay);
    for(const [key,nodes] of Object.entries(tempNodes)){nodes.label.textContent=tr(key);nodes.value.textContent=valueText(overlay[key]);}
    for(const entry of modeButtons)entry.button.textContent=tr(entry.key);
    summary.textContent=tr('values');renderActions(state);renderCharts(state);renderValues(state);
  }
  async function chooseRecord(id){picked=id;clearCharts();views.clear();renderSelectors();
    const item=records.find(item=>item.id===id);
    await model.select(id);renderSelectors();render();
  }
  source.select.addEventListener('change',()=>{group=source.select.value;picked=null;model.pause();model.select(null);clearCharts();renderSelectors();render();});
  record.select.addEventListener('change',()=>chooseRecord(record.select.value));
  episode.select.addEventListener('change',()=>{model.pause();views.clear();model.select(picked,Number(episode.select.value)).then(renderSelectors);});
  previous.addEventListener('click',()=>{model.pause();model.step(-1);});next.addEventListener('click',()=>{model.pause();model.step(1);});
  play.addEventListener('click',()=>model.get().playing?model.pause():model.play());
  seek.addEventListener('input',()=>{const index=Number(seek.value);model.pause();model.seek(index);});
  async function refresh(){
    if(disposed||!active)return;listAbort?.abort();listAbort=new AbortController();
    try{const body=await json('/api/records',{signal:listAbort.signal});if(disposed||!active)return;
      records=body.records || [];const item=records.find(r=>r.id===(picked || initialRecord));
      if(item&&initialRecord&&!picked){group=sourceOf(item);picked=item.id;initialRecord=null;await chooseRecord(item.id);}
      else if(picked && (!item || item.source_revision!==model.get().meta?.source_revision)){
        model.pause();if(item?.state==='available')await model.select(picked,model.get().episode);else await model.select(null);
      }
      renderSelectors();render();
    }catch(error){if(error.name!=='AbortError'){status.textContent=`${tr('error')}: ${error.message}`;}}
  }
  import('./scene.mjs?v=20261009').then(({createEngineScene})=>{
    if(disposed)return;try{scene=createEngineScene(engineHost,{reducedMotion:motion?.matches});scene.setTheme(document.documentElement.dataset.theme || 'light');scene.setCamera(selectedCamera);render();}
    catch{engineHost.textContent='';engineHost.hidden=true;fallback.hidden=false;}
  }).catch(()=>{engineHost.hidden=true;fallback.hidden=false;});
  const onMotion=()=>{scene?.setReducedMotion(motion.matches);render();};motion?.addEventListener?.('change',onMotion);
  renderSelectors();render();
  return {refresh,setLanguage(nextLang){lang=nextLang;renderSelectors();render();},setTheme(theme){scene?.setTheme(theme);},
    suspend(){active=false;model.pause();listAbort?.abort();for(const view of charts)view.unmount();},
    resume(){active=true;for(const view of charts)view.mount();refresh();},
    dispose(){disposed=true;listAbort?.abort();model.dispose();clearCharts();mounter.dispose();scene?.dispose();motion?.removeEventListener?.('change',onMotion);},
    getSnapshot:()=>snapshot};
}
