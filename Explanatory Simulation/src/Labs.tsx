import { useUI } from './useUI';
import { useEffect, useRef, useState } from 'react';
import { ArrowRight } from 'lucide-react';
import { api, humanWarning, localizedLabel } from './types';
import type { Frame } from './types';
export { default as ThermalLab } from './ThermalLab';

export function Slider({ label, value, min, max, step = 1, unit = '', onChange, disabled = false }: { label: string; value: number; min: number; max: number; step?: number; unit?: string; onChange: (v: number) => void; disabled?: boolean }) {
  const { format, ui, direction } = useUI();

  return <label className="slider-control" dir={direction}><span>{ui(localizedLabel(label))}<output dir="ltr"><bdi>{ui(format(value, step < .1 ? 2 : step < 1 ? 1 : 0))}</bdi> <small>{ui(unit)}</small></output></span><input type="range" min={min} max={max} step={step} value={value} disabled={disabled} aria-label={ui(localizedLabel(label))} onChange={e => onChange(+e.target.value)}/><span className="range-ends" dir="ltr"><small>{ui(min)} {ui(unit)}</small><small>{ui(max)} {ui(unit)}</small></span></label>;
}
export function EngineLab({ onFrame, onError }: { onFrame: (f: Frame) => void; onError: (e: string) => void }) {
  const { format, ui, direction } = useUI();

  const [inputs, setInputs] = useState({ rpm: 2500, map_kpa: 100, ambient_c: 25, ect_c: 90, spark: 15, lam: 1 });
  const [out, setOut] = useState<any>(); const [busy, setBusy] = useState(false);
  const sequence = useRef(0);
  const change = (key: string, v: number) => setInputs(s => ({ ...s, [key]: v }));
  async function run() { const version = ++sequence.current; setBusy(true); try { const r = await api('plant', inputs); if (version !== sequence.current) return; setOut(r); onFrame({ ...inputs, iat_k: r.iat_k, time_s: 0, speed_kmh: 0, grade_pct: 0, torque: r.torque_nm, egt_c: r.egt_c, ect_input_k: inputs.ect_c + 273.15, spark: inputs.spark, lam: inputs.lam, ki: r.knock_integral, mdot_air: r.mdot_air_gps, mdot_fuel: r.mdot_fuel_gps } as unknown as Frame); } catch (e) { onError((e as Error).message); } finally { if (version === sequence.current) setBusy(false); } }
  useEffect(() => { const timer = window.setTimeout(() => void run(), 250); return () => window.clearTimeout(timer); }, [inputs]);
  return <section className="lab-panel" dir={direction}><span className="small-label">{ui("تجربة نقطة تشغيل")}</span><h2>{ui("غيّر مدخلات المحرك، وراقب الاستجابة.")}</h2><p>{ui("تستدعي هذه التجربة ")}<code dir="ltr">plant.predict</code> {ui(" مباشرة. سرعة المحرك وضغط المانيفولد مدخلان مستقلان؛ وقد لا يمثّلان حالة ممكنة للمركبة على الطريق.")}</p><div className="lab-grid"><div>
    <Slider label="RPM" value={inputs.rpm} min={800} max={6000} step={100} unit="rpm" onChange={v => change('rpm', v)}/>
    <Slider label="Manifold pressure" value={inputs.map_kpa} min={30} max={250} unit="kPa abs" onChange={v => change('map_kpa', v)}/>
    <Slider label="Spark advance" value={inputs.spark} min={-10} max={40} unit="°BTDC" onChange={v => change('spark', v)}/>
    <Slider label="Lambda" value={inputs.lam} min={.7} max={1.25} step={.01} unit="ratio" onChange={v => change('lam', v)}/>
    <button className="primary" onClick={run} disabled={busy}>{ui(busy ? 'جارٍ حساب دورة المحرك…' : 'احسب دورة المحرك')}<ArrowRight size={16}/></button>
  </div><div className="lab-output">{out ? <><span className="badge modelled">{ui("محاكاة")}</span><dl>{[['العزم', out.torque_nm, 'Nm'], ['حرارة غاز العادم', out.egt_c, '°C'], ['تدفق الهواء', out.mdot_air_gps, 'g/s'], ['تدفق الوقود', out.mdot_fuel_gps, 'g/s'], ['مؤشر الطرق', out.knock_integral, 'ratio'], ['زاوية احتراق 50%', out.mfb50_deg, '° after TDC'], ['القدرة', out.power_kw, 'kW']].map(([name, val, unit]) => <div key={String(name)}><dt>{ui(name)}</dt><dd dir="ltr"><bdi>{ui(format(val))}</bdi> <small>{ui(unit)}</small></dd></div>)}</dl>{out.warnings?.map((s: string) => <p className="warning" key={s}>{ui(humanWarning(s))}</p>)}</> : <div className="empty">{ui("ابدأ دورة، ثم زد ضغط المانيفولد أو أخّر الشرارة وقارن الاستجابة.")}</div>}</div></div><div className="notice">{ui("الضغط المطلق يشمل الضغط الجوي، أما ضغط التعزيز فهو الزيادة فوقه. لامدا أقل من 1 تعني وقودًا أكثر لكل وحدة هواء. تنبؤات الحمل والحرارة المرتفعين والطرق غير متحقق منها.")}</div></section>;
}

