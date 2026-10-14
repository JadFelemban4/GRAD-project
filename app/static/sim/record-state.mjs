import { createChartSelection } from './chart-selection.mjs?v=R1a';

// One recording, one episode, one bounded decoded window. No inference.
export function createRecordController({readMeta,readWindow,onChange=()=>{}}) {
  let state={id:null,meta:null,episode:0,frame:null,window:null,selection:null,loading:false,reason:null,playing:false};
  let token=0,abort=null,timer=null,disposed=false;
  const emit=()=>{if(!disposed)onChange({...state});};
  const pause=()=>{clearTimeout(timer);timer=null;state.playing=false;emit();};
  function cancel(){token++;abort?.abort();abort=new AbortController();return token;}
  async function select(id,episode=0){
    pause();const request=cancel();state={id,meta:null,episode,frame:null,window:null,selection:null,loading:true,reason:null,playing:false};emit();
    if(!id){state.loading=false;emit();return;}
    try{
      const meta=await readMeta(id,{signal:abort.signal});if(request!==token||disposed)return;
      state.meta=meta;state.reason=meta.reason || null;
      state.selection=createChartSelection({sourceRevision:`${meta.source_revision}:${episode}`,axisKind:'recorded_time'});
      if(meta.state!=='available'){state.loading=false;emit();return;}
      if(!meta.episodes.some(e=>e.id===episode)){state.episode=meta.episodes[0]?.id ?? 0;
        state.selection=createChartSelection({sourceRevision:`${meta.source_revision}:${state.episode}`,axisKind:'recorded_time'});}
      await seek(0);
    }catch(error){if(request===token&&!disposed&&error.name!=='AbortError'){state.loading=false;state.reason=error.message;emit();}}
  }
  async function seek(index){
    if(disposed||state.meta?.state!=='available')return;
    const count=state.meta.episodes.find(e=>e.id===state.episode)?.samples || 0;
    index=Math.max(0,Math.min(count-1,Math.trunc(index)));if(!count||!Number.isFinite(index))return;
    const cached=state.window?.frames.find(f=>f.sample_index===index);
    if(cached){state.frame=cached;state.loading=false;state.selection.set({...state.selection.get(),sampleIndex:index});emit();return;}
    const request=cancel(),start=Math.floor(index/200)*200;
    state.frame=null;state.window=null;state.loading=true;emit();
    try{
      const window=await readWindow(state.id,state.episode,start,Math.min(200,count-start),{signal:abort.signal});
      if(request!==token||disposed)return;
      if(window.source_revision!==state.meta.source_revision){pause();state.selection.reset();state.reason='source_changed';state.loading=false;emit();return;}
      state.window=window;state.frame=window.frames.find(f=>f.sample_index===index) || null;
      state.loading=false;state.reason=state.frame?null:'missing_sample';
      if(state.frame)state.selection.set({...state.selection.get(),sampleIndex:index});emit();
    }catch(error){if(request===token&&!disposed&&error.name!=='AbortError'){pause();state.reason=error.message;state.loading=false;emit();}}
  }
  const step=delta=>seek((state.frame?.sample_index ?? 0)+delta);
  function play(){
    if(!state.frame||state.playing||disposed)return;
    state.playing=true;emit();
    const tick=async()=>{
      if(!state.playing||disposed)return;
      const sample=state.frame?.sample_index,time=state.frame?.time;
      await step(1);
      if(!state.playing||!state.frame||sample===state.frame.sample_index){pause();return;}
      const dt=state.frame.time!=null&&time!=null?state.frame.time-time:null;
      timer=setTimeout(tick,dt>0?Math.min(5000,dt*1000):150);
    };
    timer=setTimeout(tick,150);
  }
  return {get:()=>({...state}),select,seek,step,pause,play,
    dispose(){pause();disposed=true;cancel();state.window=null;state.frame=null;}};
}

export function engineOverlay(frame,channels=[]){
  const temperature=(suffix,semantic)=>{
    const channel=channels.find(c=>c.id===semantic||c.id===suffix||c.id.endsWith(`.${suffix}`));
    const value=channel&&frame?.values?.[channel.id];if(!Number.isFinite(value))return null;
    return channel.unit==='K'?value-273.15:['C','°C'].includes(channel.unit)?value:null;
  };
  return {turbine_c:temperature('t_turb','thermal.turbine'),oil_c:temperature('t_oil','thermal.oil'),block_c:temperature('t_block','thermal.block'),
    coolant_c:temperature('t_coolant','thermal.coolant'),time:frame?.time ?? null};
}

export function actuatorComparison(frame,channels=[]){
  const value=(actuator,group)=>{
    const channel=channels.find(c=>c.actuator===actuator&&c.group===group);
    const recorded=channel?.state==='recorded'?frame?.values?.[channel.id]:null;
    return {value:Number.isFinite(recorded)?recorded:null,unit:channel?.unit || null};
  };
  return ['spark','lambda','boost','fan','pump'].map(actuator=>({actuator,
    command:value(actuator,'command_trim'),applied:value(actuator,'applied_trim')}));
}
