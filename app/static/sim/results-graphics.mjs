import { H, S, T, fin, plot, line, markTip, onPointer, localXY, hline, vline } from './charts-lib.mjs?v=R1a';
import { graphicsText as text } from './graphics-strings.mjs?v=R1a';

const COLORS = ['var(--rc-sighted)','var(--rc-blind)','var(--rc-reactive)','var(--rc-grade)','var(--rc-baseline)'];
const number = value => fin(value) ? String(value) : '—';
const color = (series, i) => series.role === 'sighted' || /sighted/i.test(series.id) ? COLORS[0]
  : series.role === 'blind' || /blind/i.test(series.id) ? COLORS[1] : COLORS[i % COLORS.length];
export function numericDomain(values, zero = false) {
  let lo=Infinity,hi=-Infinity;
  for(const value of values)if(fin(value)){lo=Math.min(lo,value);hi=Math.max(hi,value);}
  if(lo===Infinity)return [0,1];
  if (zero) { lo = Math.min(0,lo); hi = Math.max(0,hi); }
  if (lo === hi) return [lo-1,hi+1];
  return [lo,hi];
}
export function panelView(panel, state) {
  const channel = panel.channels?.find(c => c.id === state.channel) || panel.channels?.[0];
  // A reader with channels puts the default in channels[0]. A panel's raw
  // series still remains available to callers when no channel was selected.
  const chosen = state.channel ? channel : null;
  return { ...panel, ...(chosen || {}), id:panel.id, kind:chosen?.kind || panel.kind,
    axes:chosen?.axes || panel.axes,
    references:chosen ? chosen.references || [] : panel.references || [],
    intervals:chosen ? chosen.intervals || [] : panel.intervals || [],
    series:(chosen?.series || panel.series || [])
      .filter(s => !(state.hidden || []).includes(s.id)), table:chosen?.table || panel.table };
}
export function exactRows(view) {
  return view.series.flatMap(series => (series.points || []).map(p => [series.label || series.id,
    p.x ?? null,p.y ?? null,p.low ?? null,p.high ?? null,p.seed ?? null,p.source_index ?? null,p.value ?? null,p.episode ?? null]));
}
function axisText(axis, lang) {
  return `${text(lang,axis?.label || '')}${axis?.unit ? ` (${text(lang,axis.unit)})` : ''}`;
}
function appendTable(parent, columns, rows, lang, select) {
  const wrap = H('div',{class:'rg-table-wrap'},parent);
  const table = H('table',{class:'rc-table'},wrap);
  const heading = H('tr',{},H('thead',{},table));
  columns.forEach(c => H('th',{scope:'col',text:text(lang,c)},heading));
  const body = H('tbody',{},table);
  let start=0;
  const pageSize=100;
  const paging=H('div',{class:'rg-controls'},parent);
  const previous=H('button',{type:'button',text:text(lang,'previous_rows')},paging);
  const position=H('span',{role:'status'},paging);
  const next=H('button',{type:'button',text:text(lang,'next_rows')},paging);
  paging.hidden=rows.length<=pageSize;
  function renderRows(){
    body.textContent='';previous.disabled=start===0;next.disabled=start+pageSize>=rows.length;
    position.textContent=`${start+1}–${Math.min(rows.length,start+pageSize)} / ${rows.length}`;
    rows.slice(start,start+pageSize).forEach((row,offset) => {
    const tr = H('tr',{},body);
    row.forEach((value,col) => {
      const td = H('td',{text:typeof value === 'number' ? number(value) : text(lang,value ?? '—')},tr);
      if (col === 0 && select) {
        td.textContent='';
        const button = H('button',{type:'button',text:String(value ?? start+offset)},td);
        button.addEventListener('click',()=>select(start+offset));
      }
    });
    });
  }
  previous.addEventListener('click',()=>{start=Math.max(0,start-pageSize);renderRows();});
  next.addEventListener('click',()=>{start=Math.min(rows.length-1,start+pageSize);renderRows();});
  renderRows();
}
export function createGraphicsPanel(panel, {lang, mounter, selection, selectionFor, viewState = {},plotHeight=null}) {
  const node = H('article',{class:'rc-figure rg-panel','data-panel':panel.id});
  const heading = H('h3',{text:panel.title || `${panel.id} · ${text(lang,panel.id)}`},node);
  H('p',{class:'rc-meta',text:panel.description || text(lang,panel.id+'_caption')},node);
  const sources = H('details',{class:'rg-source'},node);
  H('summary',{text:`${text(lang,'source')} · ${panel.source_files?.length || 0}`},sources);
  for (const file of panel.source_files || []) H('p',{class:'rc-meta',dir:'ltr',text:file},sources);
  H('p',{class:'rc-meta',dir:'ltr',text:`${text(lang,'revision')}: ${panel.revision || '—'}`},sources);
  if(panel.provenance){
    const provenance=panel.provenance;
    H('p',{class:'rc-meta',text:provenance.kind
      ?`${provenance.policy} · ${provenance.protocol} · ${provenance.source_revision} · ${text(lang,provenance.verification || 'unknown')}`
      :`${provenance.set || ''} · ${provenance.generated || '—'}`},sources);
    if(!provenance.kind)H('p',{class:'rc-note',text:text(lang,'set_score_generation_unknown')},sources);
    for(const item of provenance.training || []) H('p',{class:'rc-meta',dir:'ltr',text:
      `${item.policy}: ${item.git_commit || item.git_head || '—'} · plant ${item.plant_sha || '—'} · derived ${item.derived_sha || '—'}`},sources);
  }
  if(panel.issues?.length)H('p',{class:'rc-note',text:`${text(lang,'omissions')}: ${panel.issues.map(issue=>`${issue.policy || issue.path || ''} (${text(lang,issue.code)})`).join(' · ')}`},node);
  if(panel.omissions?.length)H('p',{class:'rc-note',text:`${text(lang,'omissions')}: ${panel.omissions.map(issue=>`${issue.policy || ''} ${issue.region || ''} (${text(lang,issue.code)})`).join(' · ')}`},node);
  if(panel.id==='G11')H('a',{class:'rg-record-link',href:`/agents?record_source=${encodeURIComponent((panel.source_files?.[0] || '').split('/').slice(0,3).join('/'))}`,text:text(lang,'open_records')},node);
  if (panel.state !== 'available') {
    H('p',{class:'rc-note rc-unavailable',text:text(lang,panel.reason || 'unavailable')},node);
    for (const caveat of panel.caveats || []) H('p',{class:'rc-note',text:text(lang,caveat)},node);
    return {node,mount(){},unmount(){}};
  }
  const controls = H('div',{class:'rg-controls'},node);
  const chart = H('div',{class:'rc-chart rg-plot',tabindex:'0','aria-label':text(lang,panel.id)},node);
  const axes = H('p',{class:'rg-axes'},node);
  const cursor = H('p',{class:'rg-cursor',role:'status','aria-live':'polite'},node);
  const legend = H('div',{class:'rg-legend'},node);
  const coverage=H('p',{class:'rc-note rg-coverage'},node);
  const details = H('details',{class:'rg-values'},node);
  details.open=Boolean(viewState.tableOpen);
  H('summary',{text:text(lang,'values')},details);
  const tableHost = H('div',{},details);
  let active = false, stop = null, current = 0, markerUpdate = () => {}, points = [], tableReady = false;
  viewState.hidden ||= [];
  if (panel.channels?.length && !panel.channels.some(c=>c.id===viewState.channel)) viewState.channel=panel.channels[0].id;
  viewState.zoom ||= 'whole';
  let channelSelect = null;
  if (panel.channels?.length > 1) {
    const label=H('label',{text:text(lang,'channel')},controls);
    channelSelect=H('select',{'aria-label':text(lang,'channel')},label);
    for (const channel of panel.channels) H('option',{value:channel.id,text:text(lang,channel.label || channel.id)},channelSelect);
    channelSelect.value=viewState.channel;
    channelSelect.addEventListener('change',()=>{ viewState.channel=channelSelect.value; viewState.hidden=[]; syncSelection(); rebuild(); });
  }
  const zoomable = !['bar','table','heatmap'].includes(panel.kind);
  let zoomSelect=null;
  if (zoomable) {
    const label=H('label',{text:text(lang,'zoom')},controls);
    zoomSelect=H('select',{'aria-label':text(lang,'zoom')},label);
    for (const key of ['whole','middle','peak']) H('option',{value:key,text:text(lang,key)},zoomSelect);
    zoomSelect.value=viewState.zoom;
    zoomSelect.addEventListener('change',()=>{ viewState.zoom=zoomSelect.value; redraw(); });
    const reset=H('button',{type:'button',text:text(lang,'reset')},controls);
    reset.addEventListener('click',()=>{viewState.zoom='whole';zoomSelect.value='whole';redraw();});
  }
  const restore=H('button',{type:'button',text:text(lang,'restore')},controls);
  restore.addEventListener('click',()=>{viewState.hidden=[];rebuild();});
  function setSelection(index) {
    if (!points.length) return;
    current=Math.max(0,Math.min(points.length-1,index));
    const point=points[current].point;
    const base=selection?.get();
    if (base) selection.set({...base, sampleIndex:base.axisKind==='pair' ? null : point.source_index ?? current,
      pairSeed:base.axisKind==='pair' ? point.seed ?? null : null});
    updateCursor(); markerUpdate();
  }
  function step(delta) {
    let index=current+delta;
    if(selection?.get().axisKind==='pair') {
      while(index>=0 && index<points.length && points[index].point.seed===points[current]?.point.seed) index+=delta;
    }
    setSelection(index);
  }
  for (const [label,delta] of [['previous',-1],['next',1]]) {
    const button=H('button',{type:'button',text:text(lang,label)},controls);
    button.addEventListener('click',()=>step(delta));
  }
  chart.addEventListener('keydown',event=>{
    if (!['ArrowLeft','ArrowRight','Home','End'].includes(event.key)) return;
    event.preventDefault();
    if(event.key==='Home' || event.key==='End')setSelection(event.key==='Home'?0:points.length-1);
    else step(event.key==='ArrowRight'?1:-1);
  });
  function updateCursor() {
    const selected=points[current];
    if (!selected) {cursor.textContent=panelView(panel,viewState).kind==='table'?'':text(lang,'empty');return;}
    const p=selected.point, view=panelView(panel,viewState);
    // For aligned line plots show all channels' series at the same source
    // sample, never interpolate. A scatter selects exactly its own mark.
    const peers=view.kind==='line' && selection?.get().axisKind!=='pair' ? view.series.flatMap(s=>(s.points || []).filter(q=>
      (p.source_index != null && q.source_index === p.source_index) || (p.source_index == null && q.x===p.x))
      .map(q=>`${text(lang,s.label || s.id)}: ${number(q.y)}`)) : [`${text(lang,selected.series.label || selected.series.id)}: ${number(p.value ?? p.y)}${view.kind==='heatmap'?` (${text(lang,view.unit || 'recorded_unit')})`:''}`];
    cursor.textContent=`${text(lang,'cursor')} ${number(p.source_index ?? current)} · ${axisText(view.axes?.x,lang)}: ${number(p.x)} · ${peers.join(' · ')}${p.seed != null ? ` · ${text(lang,'seed')}: ${p.seed}` : ''}`;
  }
  function buildTable() {
    if (tableReady) return;
    tableReady=true; tableHost.textContent='';
    const view=panelView(panel,viewState);
    if (view.table?.columns && view.table?.rows) appendTable(tableHost,view.table.columns,view.table.rows,lang);
    if (view.series.length) appendTable(tableHost,['series',axisText(view.axes?.x,lang),axisText(view.axes?.y,lang),'low','high','seed','sample','value','episode'],exactRows(view),lang,
      index=>{ const point=view.series.flatMap(s=>s.points || [])[index];setSelection(points.findIndex(q=>q.point===point)); });
  }
  details.addEventListener('toggle',()=>{viewState.tableOpen=details.open;if(details.open)buildTable();});
  function rebuild() {
    const view=panelView(panel,viewState);
    const tableOnly=view.kind==='table';
    controls.hidden=tableOnly;axes.hidden=tableOnly;legend.hidden=tableOnly;
    chart.hidden=tableOnly;
    if(tableOnly)details.open=true;
    const covered=view.coverage;
    coverage.hidden=!covered;
    coverage.textContent=covered?`${text(lang,'density_coverage')}: ${covered.included} / ${covered.total} · ${text(lang,'density_excluded')}: ${covered.excluded} · KI ${covered.ki_range.join('–')}, ${text(lang,'Recorded retard')} ${covered.retard_range.join('–')}°`:'';
    points=view.series.flatMap(series=>(series.points || []).map(point=>({series,point})));
    // Keyboard walks matched seeds together; repeated arms share one seed.
    if (selection?.get().axisKind==='pair') points.sort((a,b)=>Number(a.point.seed)-Number(b.point.seed));
    current=Math.min(current,Math.max(0,points.length-1));
    axes.textContent=view.kind==='bar' ? `${axisText(view.axes?.y,lang)} → ${axisText(view.axes?.x,lang)}` : `${axisText(view.axes?.x,lang)} → ${axisText(view.axes?.y,lang)}`;
    legend.textContent='';
    const all=panelView(panel,{...viewState,hidden:[]}).series;
    all.forEach((series,index)=>{
      const button=H('button',{type:'button',text:`${text(lang,series.label || series.id)}${series.role==='worst'?' · '+text(lang,'worst'):''}`,'aria-pressed':String(!viewState.hidden.includes(series.id))},legend);
      button.style.borderColor=color(series,index);
      button.addEventListener('click',()=>{viewState.hidden=viewState.hidden.includes(series.id)
        ? viewState.hidden.filter(id=>id!==series.id) : [...viewState.hidden,series.id];rebuild();});
    });
    for(const ref of view.references || [])H('span',{class:'rc-meta',text:`${text(lang,ref.label || 'reference_line')} · ${number(ref.value)} · ${ref.source || ''}`},legend);
    tableReady=false;tableHost.textContent='';if(details.open)buildTable();
    applySelection(selection?.get());updateCursor();redraw();
  }
  function draw(host,w,h) {
    const view=panelView(panel,viewState);
    if (view.kind==='table') {chart.hidden=true;if(!details.open){details.open=true;buildTable();}return;}
    chart.hidden=false;
    const all=view.series.flatMap(s=>s.points || []);
    const finite=all.filter(p=>fin(p.x)&&fin(p.y));
    if (!finite.length) {H('p',{class:'rc-chart-error',text:text(lang,'empty')},host);return;}
    host.querySelectorAll(':scope > .rc-chart-error').forEach(n=>n.remove());
    let xd=numericDomain(finite.map(p=>p.x));
    let yd=numericDomain(finite.flatMap(p=>[p.y,p.low,p.high]),view.kind==='bar');
    if (view.kind==='bar') {xd=[xd[0]-.6,xd[1]+.6];}
    if(view.kind==='heatmap'){
      const xs=[...new Set(finite.map(p=>p.x))].sort((a,b)=>a-b),ys=[...new Set(finite.map(p=>p.y))].sort((a,b)=>a-b);
      const dx=xs.length>1 ? Math.min(...xs.slice(1).map((x,i)=>x-xs[i])) : 1;
      const dy=ys.length>1 ? Math.min(...ys.slice(1).map((y,i)=>y-ys[i])) : 1;
      xd=[xd[0]-dx*.5,xd[1]+dx*.5];yd=[yd[0]-dy*.5,yd[1]+dy*.5];
    }
    if (viewState.zoom!=='whole') {
      const span=xd[1]-xd[0];
      const peak=viewState.zoom==='peak' ? finite.reduce((best,p)=>p.y>best.y?p:best).x : (xd[0]+xd[1])/2;
      xd=[Math.max(xd[0],peak-span/4),Math.min(xd[1],peak+span/4)];
    }
    const categorical= /category/.test(view.axes?.x?.unit || '');
    const labels=new Map(finite.map(p=>[p.x,p.label || p.policy || String(p.x)]));
    const horizontal=view.kind==='bar';
    const xSpec={d:xd,...(categorical?{ticks:[...labels.keys()],fmt:v=>labels.get(v)}:{fmt:v=>Number(v.toPrecision(4)).toString()})};
    const ySpec={d:yd,fmt:v=>Number(v.toPrecision(4)).toString()};
    if(view.axes?.x?.ticks)xSpec.ticks=view.axes.x.ticks.map(t=>t.value),xSpec.fmt=v=>view.axes.x.ticks.find(t=>t.value===v)?.label || String(v);
    if(view.axes?.y?.ticks)ySpec.ticks=view.axes.y.ticks.map(t=>t.value),ySpec.fmt=v=>view.axes.y.ticks.find(t=>t.value===v)?.label || String(v);
    const P=plot(host,{w,h,x:horizontal?ySpec:xSpec,y:horizontal?xSpec:ySpec,aria:text(lang,panel.id),m:{l:horizontal?Math.min(145,w*.35):64,r:18,t:14,b:38}});
    const pxOf=p=>horizontal?P.x(p.y):P.x(p.x),pyOf=p=>horizontal?P.y(p.x):P.y(p.y);
    for(const interval of view.intervals || [])if(fin(interval.start)&&fin(interval.end)){
      const from=Math.max(xd[0],interval.start),to=Math.min(xd[1],interval.end);
      if(to>=from)S('rect',horizontal
        ?{x:P.m.l,y:P.y(to),width:P.pw,height:P.y(from)-P.y(to),fill:'var(--rc-baseline)',opacity:.1}
        :{x:P.x(from),y:P.m.t,width:P.x(to)-P.x(from),height:P.ph,fill:'var(--rc-baseline)',opacity:.1},P.g);
    }
    for(const ref of view.references || []) {
      if(ref.axis==='identity') {
        const lo=Math.max(xd[0],yd[0]),hi=Math.min(xd[1],yd[1]);
        if(lo<=hi)line(P,[lo,hi],[lo,hi],{c:'var(--rc-baseline)',dash:'4 4'});
      } else if(fin(ref.value)) {
        if(ref.axis==='x')(horizontal?hline:vline)(P,ref.value,{c:'var(--rc-baseline)',dash:'4 4'});
        if(ref.axis==='y')(horizontal?vline:hline)(P,ref.value,{c:'var(--rc-baseline)',dash:'4 4'});
      }
    }
    const rings=[];
    view.series.forEach((series,seriesIndex)=>{
      const rows=series.points || [],c=color(series,seriesIndex);
      if(view.kind==='line' || series.kind==='line' || /ceiling/.test(series.id)) line(P,rows.map(p=>p.x),rows.map(p=>p.y),{c,dash:/measured|logged|worst|reference/.test(series.role || series.id)?'5 3':null});
      rows.forEach(p=>{
        if (!fin(p.x)||!fin(p.y)||p.x<xd[0]||p.x>xd[1])return;
        const px=pxOf(p),py=pyOf(p),pointColor=p.label==='sighted'?COLORS[0]:p.label==='blind'?COLORS[1]:c;
        let mark;
        if(view.kind==='bar'){
          const overlapping=view.series.filter(s=>(s.points || []).some(q=>q.x===p.x));
          const band=Math.min(24,P.ph/(labels.size+1)/Math.max(1,overlapping.length));
          const by=py+(overlapping.indexOf(series)-(overlapping.length-1)/2)*band;
          mark=series.role==='worst' ? S('circle',{cx:px,cy:by,r:4,fill:c},P.g)
            : S('rect',{x:Math.min(px,P.x(0)),y:by-band*.35,width:Math.max(2,Math.abs(px-P.x(0))),height:band*.7,fill:c},P.g);
        } else if(view.kind==='heatmap' && series.role!=='scenario'){
          const xs=[...new Set(finite.map(q=>q.x))].sort((a,b)=>a-b),ys=[...new Set(finite.map(q=>q.y))].sort((a,b)=>a-b);
          const cw=Math.min(56,P.pw/Math.max(1,xs.length)*.85),ch=Math.min(48,P.ph/Math.max(1,ys.length)*.85);
          const values=numericDomain(finite.map(q=>q.value));
          const intensity=fin(p.value)?(p.value-values[0])/(values[1]-values[0]):0;
          mark=S('rect',{x:px-cw/2,y:py-ch/2,width:cw,height:ch,fill:fin(p.value)?c:'none',opacity:fin(p.value)?.2+.8*intensity:1,stroke:c},P.g);
          T(P.g,px,py+4,number(p.value),{'text-anchor':'middle',class:'rc-lbl'});
        } else if(view.kind!=='line' || rows.length<70) mark=S('circle',{cx:px,cy:py,r:series.role==='scenario'?7:3.5,fill:pointColor,stroke:'var(--rc-text)','stroke-width':series.role==='scenario'?2:0},P.g);
        if(fin(p.low)&&fin(p.high)){
          if(horizontal){
            S('line',{x1:P.x(p.low),x2:P.x(p.high),y1:py,y2:py,stroke:c,'stroke-width':2},P.g);
            for(const v of [p.low,p.high])S('line',{x1:P.x(v),x2:P.x(v),y1:py-4,y2:py+4,stroke:c},P.g);
          }else{
            S('line',{x1:px,x2:px,y1:P.y(p.low),y2:P.y(p.high),stroke:c,'stroke-width':2},P.g);
            for(const v of [p.low,p.high]) S('line',{x1:px-4,x2:px+4,y1:P.y(v),y2:P.y(v),stroke:c},P.g);
          }
        }
        if(mark){
          markTip(P,mark,px,py,text(lang,series.label || series.id),[{c,v:number(view.kind==='heatmap'?p.value:p.y),k:view.kind==='heatmap'?`${text(lang,'value')} (${text(lang,view.unit || 'recorded_unit')})`:axisText(view.axes?.y,lang)},...(p.episode!=null?[{v:String(p.episode),k:text(lang,'episode')}]:[])]);
          const choose=()=>setSelection(points.findIndex(q=>q.point===p));
          mark.addEventListener('click',choose);mark.addEventListener('focus',choose);
        }
        if(view.kind!=='line' || rows.length<70){
          const ring=S('circle',{cx:px,cy:py,r:7,fill:'none',stroke:c,'stroke-width':2,visibility:'hidden'},P.top);
          rings.push({ring,p});
        }
      });
    });
    // Only one cursor mark is made for large line series (avoids thousands
    // of observer nodes); exact samples remain in the accessible table.
    const hair=S('line',{class:'rc-hair',y1:P.m.t,y2:P.H-P.m.b,visibility:'hidden'},P.top);
    markerUpdate=()=>{
      const chosen=points[current]?.point,s=selection?.get();
      rings.forEach(({ring,p})=>ring.setAttribute('visibility',s?.pairSeed != null
        ? p.seed===s.pairSeed?'visible':'hidden' : p===chosen?'visible':'hidden'));
      if(chosen && view.kind==='line' && chosen.x>=xd[0] && chosen.x<=xd[1]){
        hair.setAttribute('x1',P.x(chosen.x));hair.setAttribute('x2',P.x(chosen.x));hair.setAttribute('visibility','visible');
      } else hair.setAttribute('visibility','hidden');
    };
    if(view.kind==='line') {
      const hit=S('rect',{class:'rc-hit',x:P.m.l,y:P.m.t,width:P.pw,height:P.ph},P.top);
      onPointer(hit,event=>{
        const [px,py]=localXY(P,event),x=P.x.inv(px),paired=selection?.get().axisKind==='pair';
        let best=-1,d=Infinity;
        points.forEach((q,index)=>{
          const p=q.point;if(!fin(p.x)||!fin(p.y)||p.x<xd[0]||p.x>xd[1])return;
          const dist=paired?(pxOf(p)-px)**2+(pyOf(p)-py)**2:Math.abs(p.x-x);
          if(dist<d){d=dist;best=index;}
        });
        if(best>=0)setSelection(best);
      },()=>{});
    }
    markerUpdate();
  }
  const height=()=>plotHeight || (panelView(panel,viewState).kind==='bar' ? Math.max(310,Math.min(800,new Set(points.map(q=>q.point.x)).size*28+50)) : 310);
  function redraw(){ if(!active)return;mounter.unmount(chart);mounter.mount(chart,draw,height); }
  for(const caveat of panel.caveats || []) H('p',{class:'rc-note',text:text(lang,caveat)},node);
  function applySelection(s){
    if(!s || (s.sampleIndex==null && s.pairSeed==null))return;
    const index=points.findIndex(q=>s.pairSeed!=null ? q.point.seed===s.pairSeed : q.point.source_index===s.sampleIndex);
    if(index>=0)current=index;updateCursor();markerUpdate();
  }
  function subscribeSelection(){stop?.();stop=selection?.subscribe(applySelection);applySelection(selection?.get());}
  function syncSelection(){if(selectionFor)selection=selectionFor(panel.channels?.find(c=>c.id===viewState.channel));if(active)subscribeSelection();}
  syncSelection();rebuild();
  return {node,mount(){if(active)return;active=true;subscribeSelection();if(panelView(panel,viewState).kind!=='table')mounter.mount(chart,draw,height);},
  unmount(){active=false;stop?.();stop=null;mounter.unmount(chart);}};
}
