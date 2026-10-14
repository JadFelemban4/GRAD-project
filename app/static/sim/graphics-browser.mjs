import { H, createMounter } from './charts-lib.mjs?v=R1a';
import { GROUPS, graphicsText as text } from './graphics-strings.mjs?v=R1a';
import { createChartSelection } from './chart-selection.mjs?v=R1a';
import { createGraphicsPanel } from './results-graphics.mjs?v=R1a';

// Cache choices and UI preferences, but mount only the active group's plots.
export function createGraphicsBrowser(host, {onGroup = ()=>{}} = {}) {
  const choices=new Map();
  const mounter=createMounter({onError:(chart)=>{H('p',{class:'rc-chart-error',text:text(currentLang,'unavailable')},chart);}});
  let current=null,currentLang='ar',active=[],observer=null,signature='';
  const IO=globalThis.IntersectionObserver;
  if(typeof IO==='function') observer=new IO(entries=>{
    for(const entry of entries){ const panel=active.find(p=>p.node===entry.target);if(!panel)continue;
      if(entry.isIntersecting)panel.mount();else panel.unmount(); }
  },{rootMargin:'200px'});
  function detach(){for(const panel of active){observer?.unobserve(panel.node);panel.unmount();}active=[];}
  function render({sourceKey,panels=[],lang,title,updating=false,recorderTest=false,externalGroups={}}) {
    currentLang=lang;
    const nextSignature=JSON.stringify([sourceKey,lang,panels,title,updating,recorderTest,externalGroups]);
    if(signature===nextSignature)return;
    signature=nextSignature;detach();host.textContent='';
    const countOf=group=>panels.filter(p=>p.group===group).length+(externalGroups[group] || 0);
    if(!GROUPS.some(group=>countOf(group))){host.hidden=true;return;}
    host.hidden=false;
    let choice=choices.get(sourceKey);
    if(!choice){choice={group:countOf('overview')?'overview':countOf('evaluation')?'evaluation':GROUPS.find(group=>countOf(group)),
      views:new Map(),stores:new Map(),panels:new Map()};choices.set(sourceKey,choice);}
    current=choice;
    H('h2',{text:title},host);
    if(recorderTest)H('p',{class:'rc-note',text:text(lang,'recorder')},host);
    if(updating)H('p',{class:'rc-note',text:text(lang,'last_valid')},host);
    const nav=H('nav',{class:'rg-nav','aria-label':text(lang,'groups')},host);
    const grid=H('div',{class:'rg-grid'},host);
    const buttons=new Map();
    for(const group of GROUPS){
      const count=countOf(group);
      const button=H('button',{type:'button',text:`${text(lang,group)} · ${count}`,'aria-pressed':String(choice.group===group)},nav);
      button.disabled=!count;buttons.set(group,button);
      button.addEventListener('click',()=>{choice.group=group;mountGroup();});
    }
    function mountGroup(){
      detach();grid.textContent='';
      for(const [group,button] of buttons)button.setAttribute('aria-pressed',String(group===choice.group));
      onGroup(choice.group);
      for(const panel of panels.filter(p=>p.group===choice.group)){
        const key=panel.id;
        const panelSignature=JSON.stringify([lang,panel]);
        let rendered=choice.panels.get(key);
        if(rendered?.signature!==panelSignature){
          rendered?.unmount();
          const previous=choice.views.get(key);
          const viewState=previous && previous.revision===panel.revision?previous.state:{};
          choice.views.set(key,{revision:panel.revision,state:viewState});
          const paired=['G07','G08','G12'].includes(panel.id);
          const alignment=['G01','G02'].includes(panel.id)?'historical_episode':panel.alignment || panel.id;
          const axisKind=paired?'pair':`${alignment}:${panel.source_files?.join('|')}:${panel.axes?.x?.label}:${panel.axes?.x?.unit}`;
          // Pair panels share only this set's generation; time panels share
          // only identical source files and axis units. Training stays separate.
          const generation=paired ? panels.filter(p=>['G07','G08','G12'].includes(p.id)).map(p=>p.revision).join(':') : panel.revision;
          const storeKey=`${axisKind}:${generation}`;
          if(!choice.stores.has(storeKey))choice.stores.set(storeKey,createChartSelection({sourceRevision:`${sourceKey}:${generation}`,axisKind}));
          const selectionFor=panel.id==='G11' ? channel=>{
            const alignment=channel?.alignment || panel.id,recordKey=`record:${panel.revision}:${alignment}`;
            if(!choice.stores.has(recordKey))choice.stores.set(recordKey,createChartSelection({sourceRevision:`${sourceKey}:${panel.revision}:${alignment}`,axisKind:'recorded_time'}));
            return choice.stores.get(recordKey);
          } : undefined;
          rendered={...createGraphicsPanel(panel,{lang,mounter,viewState,selection:choice.stores.get(storeKey),selectionFor}),signature:panelSignature};
          choice.panels.set(key,rendered);
        }
        grid.appendChild(rendered.node);active.push(rendered);
        if(observer)observer.observe(rendered.node);else rendered.mount();
      }
    }
    if(!countOf(choice.group))choice.group=GROUPS.find(group=>countOf(group));
    mountGroup();
  }
  return {render,dispose(){detach();observer?.disconnect();mounter.dispose();choices.clear();signature='';},
    suspend(){detach();},resume(){for(const panel of active)panel.mount();}};
}
