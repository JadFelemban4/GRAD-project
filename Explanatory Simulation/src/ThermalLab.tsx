import { useUI } from './useUI';
import { useEffect, useRef, useState } from 'react';
import { api } from './types';
import type { Frame } from './types';
import { Slider } from './Labs';
import { axis, comparison, requestGate, restoreReference, sharedAt, snapshot } from './model/thermal-comparison.mjs';
import type { ThermalRequest, ThermalRun } from './model/thermal-comparison.mjs';
const initial:ThermalRequest = { rpm:3000, map_kpa:180, ambient_c:42, spark:8, lam:.92, fan:1, pump:1, heat_s:30, cool_s:90 };
const nodes = [['t_block','الكتلة / سائل التبريد'],['t_oil','الزيت'],['t_turb','هيكل التوربين']];
const names:Record<string,string> = {fan:'المروحة',pump:'المضخة',heat_s:'مدة التسخين',cool_s:'مدة التبريد',rpm:'RPM',map_kpa:'MAP',ambient_c:'الجو',spark:'الشرارة',lam:'لامدا',method:'طريقة المصدر',initial_state:'حالة البدء',initial_frame:'قيم إطار البدء'};
export const thermalPhase = (phase:string) => phase === 'heating' ? 'تسخين' : phase === 'cooling' ? 'تبريد · RPM 800، وقود وعادم صفر' : 'بداية باردة';
function ThermalChart({ reference, current, node, title, time }: {reference:any[];current:any[];node:string;title:string;time:number}) {
  const { format, ui, uiTemplate } = useUI();

  const scale = axis(reference,current,node);
  const x = (t:number) => 48 + t / scale.timeMax * 520;
  const y = (k:number) => 166 - ((k-273.15)-scale.min) / (scale.max-scale.min)*140;
  const path = (frames:any[]) => {
    let connected = false;
    return frames.map(f => {
      if (typeof f[node] !== 'number' || !Number.isFinite(f[node]) || !Number.isFinite(f.time_s)) { connected=false; return ''; }
      const command = `${connected?'L':'M'}${x(f.time_s)},${y(f[node])}`; connected=true; return command;
    }).join(' ');
  };
  return <figure className="thermal-chart"><figcaption>{ui(title)} · °C</figcaption><svg viewBox="0 0 600 205" role="img" aria-label={ui(uiTemplate("{0}: المرجع متقطع، النتيجة الحالية متصلة، محور حرارة مشترك", "{0}: dashed reference, solid current result, shared temperature axis", title))} style={{direction:"ltr"}}>
    {[0,.5,1].map(n=><g key={n}><line x1={48} x2={568} y1={166-n*140} y2={166-n*140} stroke="#536171" strokeOpacity=".45"/><text x={43} y={170-n*140} textAnchor="end">{ui(format(scale.min+n*(scale.max-scale.min),0))}</text></g>)}
    <path d={path(reference)} fill="none" stroke="#cba2f2" strokeWidth={3} strokeDasharray="8 5"/><path d={path(current)} fill="none" stroke="#5ed7dc" strokeWidth={2}/>
    <line x1={x(time)} x2={x(time)} y1={26} y2={166} stroke="#f6df99" strokeDasharray="3 3"/>
    <text x={48} y={193}>0 s</text><text x={568} y={193} textAnchor="end">{ui(scale.timeMax)} s</text>
  </svg></figure>;
}
export default function ThermalLab({onError,onFrame}:{onError:(e:string)=>void;onFrame:(f:Frame)=>void}) {
  const { format, ui, uiTemplate, direction } = useUI();

  const [draft,setDraft] = useState<ThermalRequest>({...initial});
  const [current,setCurrent] = useState<ThermalRun|null>(null);
  const [reference,setReference] = useState<ThermalRun|null>(null);
  const [cursor,setCursor] = useState(0);
  const [busy,setBusy] = useState(false);
  const gate = useRef(requestGate());
  const lock = useRef(false);
  useEffect(()=>()=>gate.current.cancel(),[]);
  const f = current?.frames[cursor];
  useEffect(()=>{if(f)onFrame(f);},[f,onFrame]);
  const status = comparison(reference,current);
  const draftStatus = reference ? comparison(reference,{...reference,request:draft}) : null;
  const pending = !!current && Object.keys(draft).some(k=>draft[k as keyof ThermalRequest]!==current.request[k as keyof ThermalRequest]);
  const pair = reference && current && status.valid && f ? sharedAt(reference.frames,current.frames,f.time_s) : null;
  async function run() {
    if(lock.current)return;
    lock.current=true;setBusy(true);
    const request={...draft}, version=gate.current.begin();
    try {
      const response=await api('thermal',request);
      if(!gate.current.accept(version))return;
      const result=snapshot(request,response);setCurrent(result);setCursor(result.frames.length-1);
    } catch(e) {if(gate.current.accept(version))onError((e as Error).message);}
    finally {if(gate.current.accept(version)){setBusy(false);lock.current=false;}}
  }
  function restore() {
    if(!reference)return;
    gate.current.cancel();lock.current=false;setBusy(false);
    const restored=restoreReference(reference);setDraft(restored.draft);setCurrent(restored.run);setCursor(restored.run.frames.length-1);
  }
  const change=(key:keyof ThermalRequest,v:number)=>setDraft(old=>({...old,[key]:v}));
  return <section className="lab-panel thermal-experiment" dir={direction} aria-label={ui("تجربة المروحة والمضخة المستقلة")}>
    <span className="small-label">{ui("تجربة مستقلة · ThermalNetwork")}</span><h2>{ui("ثبّت المرجع، ثم غيّر التبريد.")}</h2>
    <p>{ui("المروحة والمضخة تعدّلان فقد الرديتر عبر منظم النموذج. لا يوجد اتصال مباشر منهما إلى عقدة التوربين؛ تساوي منحناه أو انغلاق المنظم نتيجة مفيدة.")}</p>
    <details open><summary>{ui("إعدادات المسودة · لا تطبّق حتى التشغيل")}</summary><div className="thermal-draft-grid">
      <Slider label="Heating duration" value={draft.heat_s} min={5} max={120} step={5} unit="s" onChange={v=>change('heat_s',v)}/>
      <Slider label={ui("المروحة")} value={draft.fan} min={0} max={1} step={.05} unit="fraction" onChange={v=>change('fan',v)}/>
      <Slider label={ui("المضخة")} value={draft.pump} min={.3} max={1} step={.05} unit="fraction" onChange={v=>change('pump',v)}/>
    </div><p>{ui("نقطة التسخين الثابتة: ")}<bdi style={{direction:"ltr"}}>RPM 3000 · MAP 180 kPa abs · spark 8°BTDC · λ 0.92</bdi>{ui(". الجو 42°C، التبريد 90 s، بدء جميع العقد عند الجو، تكامل المصدر 0.1 s.")}</p></details>
    {pending&&<p className="warning" role="status">{ui("المسودة تغيّرت؛ القيم والمنحنيات أدناه تخص آخر تشغيل محفوظ.")}</p>}
    {reference&&<p>{ui("تغييرات المسودة عن المرجع: ")}{ui(draftStatus?.changed.length ? draftStatus.changed.map(k=>`${ui(names[k]||k)}: ${reference.request[k as keyof ThermalRequest]} → ${draft[k as keyof ThermalRequest]}`).join(' · ') : 'لا تغيير')}{ui(draftStatus&&!draftStatus.valid&&' · مقارنة التبريد غير صالحة: أعد إعدادات المرجع أو شغّل ثم ثبّت مرجعًا جديدًا.')}</p>}
    <div className="button-row"><button className="primary" onClick={()=>void run()} disabled={busy}>{ui(busy?'جارٍ حساب المصدر…':reference?'شغّل إعدادات المسودة من البدء نفسه':'شغّل التسخين والتبريد')}</button><button disabled={!current||busy} onClick={()=>setReference(current)}>{ui("ثبّت النتيجة الحالية مرجعًا")}</button><button disabled={!reference||busy} onClick={restore}>{ui("استعد إعدادات المرجع ونتيجته")}</button></div>
    {current&&<><p className="thermal-applied">{ui("النتيجة المحفوظة: مروحة ")}{ui(current.request.fan)}{ui("، مضخة ")}{ui(current.request.pump)}{ui("، تسخين ")}{ui(current.request.heat_s)} {ui(" s، تبريد ")}{ui(current.request.cool_s)} s. {ui(reference&&uiTemplate("المرجع: مروحة {0}، مضخة {1}، تسخين {2} s.", "Reference: fan {0}, pump {1}, heating {2} s.", reference.request.fan, reference.request.pump, reference.request.heat_s))}</p>
      <p role="status">{ui(reference?(status.valid?status.changed.length?uiTemplate("مقارنة صالحة · المتغيّر: {0}", "Valid comparison · changed: {0}", status.changed.map(k=>ui(names[k]||k)).join(' + ')):'مقارنة صالحة · الإعدادات متساوية':uiTemplate("مقارنة غير صالحة · تغيّر {0}؛ الفروق غير معروضة", "Invalid comparison · changed {0}; differences hidden", status.invalid.map(k=>ui(names[k]||k)).join(' + '))):'ثبّت النتيجة مرجعًا لإظهار الفروق.')}</p>
      <label className="thermal-cursor">{ui("اختر زمن المصدر: ")}<bdi style={{direction:"ltr"}}>{ui(format(f?.time_s,1))} s</bdi> · {ui(thermalPhase(f?.phase))}<input aria-label={ui("المؤشر الزمني للتجربة الحرارية")} type="range" min={0} max={current.frames.length-1} value={cursor} onChange={e=>setCursor(+e.target.value)}/></label>
      <div className="thermal-values">{nodes.map(([key,name])=>{const value=pair?.values[key];const delta=value?.delta;return <div key={key}><small>{ui(name)}</small><strong style={{direction:"ltr"}}>{ui(format(typeof f?.[key]==='number'?f[key]-273.15:undefined))} °C</strong><span>{ui("المرجع عند الزمن نفسه: ")}<bdi style={{direction:"ltr"}}>{ui(format(value?.reference))} °C</bdi></span><span>{ui("الحالي − المرجع: ")}<bdi style={{direction:"ltr"}}>{ui(delta==null?'غير متاح':`${delta>0?'+':''}${delta.toFixed(3)} °C`)}</bdi></span></div>;})}</div>
      {reference&&status.valid&&!pair&&<p>{ui("لا توجد عينة مشتركة عند هذا الزمن الفعلي؛ لا نستوفي قيمًا بين العينات.")}</p>}
      <p className="thermal-chart-legend"><span>{ui("━━ النتيجة الحالية")}</span>{reference&&status.valid?<><span> {ui(" ┄┄ المرجع")}</span> {ui(" · الزمن المنقضي نفسه، ومحور حرارة مشترك لكل عقدة")}</>:<> {ui(" · منحنى النتيجة المحفوظة فقط؛ ")}{ui(reference?'المقارنة غير صالحة':'لم يُثبّت مرجع بعد')}</>}</p>
      <div className="thermal-charts">{nodes.map(([node,title])=><ThermalChart key={node} reference={reference&&status.valid?reference.frames:[]} current={current.frames} node={node} title={ui(title)} time={f?.time_s??0}/>)}</div>
    </>}
    <details><summary>{ui("طريقة المصدر وحدود التجربة")}</summary><p>{ui("التسخين يستخدم plant.predict عند نقطة ثابتة وECT=الجو، وحرارة الشحنة الافتراضية أعلى من الجو 12 K دون مدخل من الكتلة. التبريد: RPM 800، تدفق الوقود والعادم صفر؛ حد الغاز هو الجو وحرارة غاز العادم غير متاحة. المحرك ليس متوقفًا بالكامل. معاملات الحاوية افتراضية، وعقدة الكتلة المعايرة تتذبذب عند خطوات كبيرة؛ نستخدم تكامل المصدر 0.1 s.")}</p><p>{ui("حالة البدء: ")}{ui(current?.initial_state||'cold_start_at_ambient')}</p>{current&&<p style={{direction:"ltr"}}>{ui(current.method)}</p>}</details>
  </section>;
}

