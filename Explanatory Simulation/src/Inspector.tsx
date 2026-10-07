import { useUI } from './useUI';
import { ProvenanceDrawer } from './ProvenanceDrawer';
import { registerModal } from './modal-stack.mjs';
import { useEffect, useRef, useState } from 'react';
import { ArrowRight, Code2, ExternalLink, X } from 'lucide-react';
import { api, conceptCopy, evidenceLabel } from './types';
import type { Concept, Frame, Meta, ReadingContext, Road } from './types';
import { readingLabel } from './model/reading-label.mjs';
import { resolveReading } from './model/reading-context.mjs';
import { usePreferences } from './Preferences';
import { PressureDiagram } from './PressureDiagram';
import { pressureReading } from './model/pressure.mjs';
import { turboFlowData } from './model/turbo-layout.mjs';

export function Evidence({ value }: { value?: string }) {
  const { ui, direction } = useUI();

  const raw = value || 'UNVERIFIED';
  return <span className={`badge ${raw.toLowerCase().replaceAll(' ', '-')}`} dir={direction}>{ui(evidenceLabel(value))}</span>;
}

export function conceptValue(id: string, f: Frame | null) {
  if (!f) return undefined;
  const celsius = (key: string) => typeof f[key] === 'number' && Number.isFinite(f[key]) ? f[key] - 273.15 : undefined;
  const map: Record<string, any> = { engine_torque: f.torque, t_turb: celsius('t_turb'), t_oil: celsius('t_oil'), t_block: celsius('t_block'), egt: f.egt_c, grade: f.grade_pct, fuel: f.mdot_fuel, air: f.mdot_air, map: f.map_kpa, knock: f.ki, damage: f.damage_rate, lambda: f.lam, gear: f.gear, fan_duty: f.command?.[3], pump_duty: f.command?.[4] };
  if (id === 'exhaust_flow') return turboFlowData(f).exhaust;
  return Object.hasOwn(map,id) ? map[id] : f[id];
}

export function Inspector({ concept, meta, frame, readingContext, readingFrame, previousFrame, sessionId = '', pressureSessionId = '', preview, road, onSelect, onSource }: { concept?: Concept; meta: Meta; frame: Frame | null; readingContext?: ReadingContext | null; readingFrame?: Frame | null; previousFrame?: Frame; sessionId?: string; pressureSessionId?: string; preview?: boolean; road?: Road; onSelect: (id: string) => void; onSource: (s: any) => void }) {
  const { format, ui } = useUI();

  const { t, direction, language } = usePreferences();
  if (!concept) return <div className="inspector empty" dir={direction}>{ui("اختر جزءًا من السيارة أو متغيرًا لتتبّع أسبابه ونتائجه.")}</div>;
  const reading = resolveReading(readingContext, {frame: readingFrame, previousFrame, sessionId, previousSessionId:sessionId, conceptId:concept.id, preview, road});
  const pressure = concept.id === 'barometric_pressure' ? pressureReading(frame, pressureSessionId) : null;
  const value = pressure ? pressure.value : reading ? reading.value : conceptValue(concept.id, frame);
  const copy = conceptCopy(concept);
  const names = (id: string) => { const item = meta.concepts.find(c => c.id === id); return item ? conceptCopy(item).name : id; };
  const caveat = copy.caveat;
  return <aside className="inspector" dir={direction}><div className="section-head"><span className="small-label">{ui("داخل المشروع")}</span><Code2 size={16}/></div><h2>{ui(copy.name)}</h2><Evidence value={concept.evidence}/><p className="meaning">{ui(copy.meaning)}</p>
    {reading && <p className="reading-context"><span>{readingLabel(reading, language)} · {ui({baseline:'مرجع ECU',requested:'الطلب الفيزيائي',input:'دخل القرار',applied:'الأمر المطبّق',interval:'نتيجة الفترة',end:'حالة النهاية'}[reading.phase])}</span><br/><bdi dir="ltr">{ui(reading.phase==='interval'?`${format(reading.inputS,0)}–${format(reading.endS,0)}`:format(reading.phase==='end'?reading.endS:reading.inputS,0))} s</bdi></p>}
    <div className="current-value"><strong><bdi dir="ltr">{ui(pressure && pressure.value === null ? t('غير متاح','Unavailable') : format(value,reading?.digits ?? 1))}</bdi></strong><span dir="ltr">{ui(reading ? reading.unit : ['t_turb','t_oil','t_block'].includes(concept.id) ? '°C' : concept.unit)}</span></div>
    {pressure && <p className="reading-context" data-testid="pressure-reading-context">{ui(t('مدخل السيناريو · زمن الدخل','Scenario input · input time'))}: <bdi dir="ltr">{ui(pressure.inputS === null ? t('غير متاح','Unavailable') : `${pressure.inputS.toFixed(1)} s`)}</bdi><br/><code dir="ltr">{pressure.source}</code></p>}
    {['barometric_pressure','map','turbo','air'].includes(concept.id) && <PressureDiagram key={concept.id} frame={frame} sessionId={pressureSessionId} onSource={onSource}/>}
    <ProvenanceDrawer concept={concept} value={value} reading={reading} frame={reading ? readingFrame : frame} pressure={pressure} onSource={onSource}/>
    <h4>{ui("لماذا يهم؟")}</h4><p>{ui(copy.why)}</p>{concept.range != null && <p className="subtle">{ui("حدود المشروع: ")}<bdi dir="auto">{ui(typeof concept.range === 'string' ? concept.range : JSON.stringify(concept.range))} {ui(concept.unit)}</bdi>{ui(". هذا ليس نطاق تشغيل آمنًا متحققًا منه.")}</p>}<h4>{ui("ما الذي يغيّره؟")}</h4><div className="chain-links">{concept.upstream.map(id => <button key={id} onClick={() => onSelect(id)}>{ui(names(id))}<ArrowRight size={12}/></button>)}</div><h4>{ui("ما الذي يتأثر به؟")}</h4><div className="chain-links">{concept.downstream.map(id => <button key={id} onClick={() => onSelect(id)}>{ui(names(id))}<ArrowRight size={12}/></button>)}</div>
    {(copy.increase || copy.decrease) && <details><summary>{ui("إذا غيّرت قيمته")}</summary>{copy.increase && <p>{ui("عند الزيادة: ")}{ui(copy.increase)}</p>}{copy.decrease && <p>{ui("عند الخفض: ")}{ui(copy.decrease)}</p>}</details>}
    {caveat && <p className="warning">{ui(caveat)}</p>}
    <div className="source-card" dir={direction}><code dir="ltr">{concept.source.variable || concept.id}</code><span dir="ltr">{ui(concept.source.file)}:{ui(concept.source.line)}</span><small dir="ltr">{ui(concept.source.symbol)}</small><button onClick={() => onSource(concept.source)}>{ui("افتحه في ملفات المشروع")}<ExternalLink size={13}/></button></div>
  </aside>;
}

export function SourceDialog({ source, onClose }: { source: any; onClose: () => void }) {
  const { message, ui, direction } = useUI();

  const [data, setData] = useState<any>(); const [error, setError] = useState('');
  useEffect(() => { setData(undefined); setError(''); api(`source?file=${encodeURIComponent(source.file)}&line=${source.line}`).then(setData).catch(e => setError(e.message)); }, [source]);
  const sourceDialog = useRef<HTMLElement | null>(null);
  const closeSource = useRef(onClose);
  closeSource.current = onClose;
  useEffect(() => {
    if (!sourceDialog.current) return;
    return registerModal(document, { element: sourceDialog.current, onClose: () => closeSource.current() });
  }, []);
  return <div className="dialog-backdrop" onClick={onClose}><section ref={sourceDialog} tabIndex={-1} className="source-dialog" role="dialog" aria-modal="true" aria-label={ui("مقتطف من الشيفرة الأصلية")} onClick={e => e.stopPropagation()} dir={direction}><div className="section-head"><div><span className="small-label">{ui("مصدر للقراءة فقط")}</span><h2 dir="ltr">{ui(source.file)}</h2></div><button aria-label={ui("إغلاق المصدر")} onClick={onClose}><X size={20}/></button></div><p dir="ltr">{ui(source.symbol)} · {ui(source.variable)} {ui(" · السطر ")}{ui(source.line)}</p>{error && <div className="error">{message(error)}</div>}{!data && !error && <p>{ui("جارٍ قراءة المصدر المحلي…")}</p>}<div className="source-code" dir="ltr">{data && (Array.isArray(data.lines) ? data.lines.map((row: any, i: number) => <div key={i} className={(row.line ?? row.number) === source.line ? 'active-line' : ''}><span>{ui(row.line ?? row.number ?? i + (data.start_line || 1))}</span><code dir="ltr">{row.text ?? row.content ?? row}</code></div>) : <pre dir="ltr">{data.text || data.content || JSON.stringify(data, null, 2)}</pre>)}</div><p className="subtle">{ui("يعرض هذا المقتطف ملفات المشروع المحلية الحالية. لا يمكن للمتصفح تعديلها.")}</p></section></div>;
}


