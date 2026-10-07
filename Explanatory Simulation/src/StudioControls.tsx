import { useUI } from './useUI';
import { useEffect, useRef, useState } from 'react';
import { api, humanWarning } from './types';
import type { Frame } from './types';
import { captureOperatingBaseline, compareOperatingResults } from './model/operating-comparison.mjs';
import type { OperatingBaseline, OperatingInputs } from './model/operating-comparison.mjs';

type InputKey = keyof OperatingInputs;

const fields: { key: InputKey; label: string; min: number; max: number; step: number; unit: string; digits: number }[] = [
  { key: 'rpm', label: 'سرعة المحرك', min: 800, max: 6000, step: 100, unit: 'rpm', digits: 0 },
  { key: 'map_kpa', label: 'ضغط المانيفولد', min: 30, max: 250, step: 1, unit: 'kPa abs', digits: 0 },
  { key: 'spark', label: 'تقديم الشرارة', min: -10, max: 40, step: 1, unit: '°BTDC', digits: 0 },
  { key: 'lam', label: 'لامدا', min: 0.7, max: 1.25, step: 0.01, unit: 'ratio', digits: 2 },
];

const initial: OperatingInputs = { rpm: 2500, map_kpa: 100, spark: 15, lam: 1 };

function inputText(value: number, digits: number) {
  return value.toFixed(digits);
}

export function StudioOperatingControls({ active, onFrame, onError }: { active: boolean; onFrame: (frame: Frame) => void; onError?: (message: string) => void }) {
  const { format, message, ui, uiTemplate, direction } = useUI();

  const [inputs, setInputs] = useState<OperatingInputs>(initial);
  const [drafts, setDrafts] = useState<Record<InputKey, string>>({ rpm: '2500', map_kpa: '100', spark: '15', lam: '1.00' });
  const [result, setResult] = useState<any>();
  const [resultInputs, setResultInputs] = useState<OperatingInputs | null>(null);
  const [baseline, setBaseline] = useState<OperatingBaseline | null>(null);
  const [warnings, setWarnings] = useState<string[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const sequence = useRef(0);
  const mounted = useRef(false);
  const activeRef = useRef(active);
  const onFrameRef = useRef(onFrame);
  const onErrorRef = useRef(onError);
  activeRef.current = active;
  onFrameRef.current = onFrame;
  onErrorRef.current = onError;

  useEffect(() => {
    mounted.current = true;
    return () => { mounted.current = false; sequence.current++; };
  }, []);

  useEffect(() => {
    const version = ++sequence.current;
    if (!active) {
      setBusy(false);
      return;
    }

    setBusy(true);
    setError('');
    setWarnings([]);
    const timer = window.setTimeout(async () => {
      try {
        const r = await api('plant', { rpm: inputs.rpm, map_kpa: inputs.map_kpa, ambient_c: 25, ect_c: 90, spark: inputs.spark, lam: inputs.lam });
        if (!mounted.current || version !== sequence.current || !activeRef.current) return;
        setResult(r);
        setResultInputs({ ...inputs });
        setWarnings(Array.isArray(r.warnings) ? r.warnings : []);
        onFrameRef.current({
          ...inputs,
          ambient_c: 25,
          ect_c: 90,
          iat_k: r.iat_k,
          time_s: 0,
          speed_kmh: 0,
          grade_pct: 0,
          torque: r.torque_nm,
          egt_c: r.egt_c,
          ect_input_k: 90 + 273.15,
          ki: r.knock_integral,
          mdot_air: r.mdot_air_gps,
          mdot_fuel: r.mdot_fuel_gps,
        } as unknown as Frame);
      } catch (e) {
        if (!mounted.current || version !== sequence.current || !activeRef.current) return;
        const message = (e as Error).message;
        setError(message);
        onErrorRef.current?.(message);
      } finally {
        if (mounted.current && version === sequence.current) setBusy(false);
      }
    }, 250);

    return () => {
      window.clearTimeout(timer);
      if (sequence.current === version) sequence.current++;
    };
  }, [active, inputs]);

  function update(key: InputKey, value: number) {
    const field = fields.find(item => item.key === key)!;
    const next = Math.max(field.min, Math.min(field.max, value));
    setInputs(current => ({ ...current, [key]: next }));
    setDrafts(current => ({ ...current, [key]: inputText(next, field.digits) }));
  }

  function commitDraft(key: InputKey) {
    const field = fields.find(item => item.key === key)!;
    const parsed = Number(drafts[key]);
    if (!drafts[key].trim() || !Number.isFinite(parsed)) {
      setDrafts(current => ({ ...current, [key]: inputText(inputs[key], field.digits) }));
      return;
    }
    const clamped = Math.max(field.min, Math.min(field.max, parsed));
    const snapped = field.min + Math.round((clamped - field.min) / field.step) * field.step;
    const value = Math.max(field.min, Math.min(field.max, Number(snapped.toFixed(field.digits))));
    update(key, value);
  }

  function restoreBaseline() {
    if (!baseline) return;
    const restored = { ...baseline.inputs };
    setInputs(restored);
    setDrafts({
      rpm: inputText(restored.rpm, 0),
      map_kpa: inputText(restored.map_kpa, 0),
      spark: inputText(restored.spark, 0),
      lam: inputText(restored.lam, 2),
    });
  }

  const comparison = baseline && result ? compareOperatingResults(result, baseline) : [];
  const inputPoint = (values: OperatingInputs) => <span className="studio-comparison__point" dir="ltr"><bdi>{ui(format(values.rpm, 0))} rpm</bdi> · <bdi>{ui(format(values.map_kpa, 0))} kPa</bdi> · <bdi>{ui(format(values.spark, 0))}°</bdi> · <bdi>{ui(format(values.lam, 2))} λ</bdi></span>;
  const signedDelta = (delta: number | null) => delta === null ? 'غير متاح' : `${delta > 0 ? '+' : ''}${format(delta)}`;

  return <section className="studio-operating" aria-label={ui("تجربة نقطة تشغيل المحرك")} hidden={!active} dir={direction}>
    <header className="studio-operating__header">
      <span className="studio-operating__eyebrow">{ui("نقطة تشغيل مباشرة")}</span>
      <h2 className="studio-operating__title">{ui("مدخلات المحرك")}</h2>
      <p>{ui("غيّر مدخلًا لمعاينة استجابة المحرك.")}</p>
    </header>

    <div className="studio-operating__grid">
      {fields.map(field => <div className="studio-operating__control" key={field.key}>
        <div className="studio-operating__control-head">
          <label htmlFor={`studio-${field.key}-number`}>{ui(field.label)}</label>
          <span className="studio-operating__readout" dir="ltr"><input id={`studio-${field.key}-number`} className="studio-operating__number" type="number" inputMode="decimal" min={field.min} max={field.max} step={field.step} value={drafts[field.key]} disabled={!active} aria-label={ui(uiTemplate("{0}، إدخال رقمي", "{0}, numeric input", field.label))} onChange={e => setDrafts(current => ({ ...current, [field.key]: e.target.value }))} onBlur={() => commitDraft(field.key)} onKeyDown={e => { if (e.key === 'Enter') e.currentTarget.blur(); }}/><small>{ui(field.unit)}</small></span>
        </div>
        <input className="studio-operating__slider" type="range" min={field.min} max={field.max} step={field.step} value={inputs[field.key]} disabled={!active} aria-label={ui(field.label)} onChange={e => update(field.key, Number(e.target.value))}/>
      </div>)}
    </div>

    <div className="studio-operating__results" aria-live="polite">
      <div className="studio-operating__status">{ui(busy ? (result ? 'جارٍ الحساب · تظهر آخر نتيجة' : 'جارٍ الحساب…') : error ? (result ? 'تعذّر الحساب · تظهر آخر نتيجة' : 'تعذّر الحساب') : result ? 'نتيجة النموذج' : 'بانتظار المدخلات')}</div>
      {error && <p className="studio-operating__error">{message(error)}</p>}
      {result && <dl>
        <div><dt>{ui("العزم")}</dt><dd dir="ltr"><bdi>{ui(format(result.torque_nm))}</bdi> <small>Nm</small></dd></div>
        <div><dt>{ui("حرارة غاز العادم")}</dt><dd dir="ltr"><bdi>{ui(format(result.egt_c))}</bdi> <small>°C</small></dd></div>
        <div><dt>{ui("تدفق الوقود")}</dt><dd dir="ltr"><bdi>{ui(format(result.mdot_fuel_gps))}</bdi> <small>g/s</small></dd></div>
        <div><dt>{ui("تدفق الهواء")}</dt><dd dir="ltr"><bdi>{ui(format(result.mdot_air_gps))}</bdi> <small>g/s</small></dd></div>
      </dl>}
    </div>

    <section className="studio-baseline" aria-label={ui("مقارنة مرجعية")}>
      <div className="studio-baseline__actions">
        <button type="button" disabled={!active || busy || !!error || !result || !resultInputs} onClick={() => {
          if (busy || error || !result || !resultInputs) return;
          setBaseline(captureOperatingBaseline({ inputs: resultInputs, result }));
        }}>{ui("ثبّت المرجع")}</button>
        <button type="button" disabled={!active || !baseline} onClick={restoreBaseline}>{ui("ارجع للمرجع")}</button>
        <button type="button" disabled={!baseline} onClick={() => setBaseline(null)}>{ui("امسح المرجع")}</button>
      </div>
      {baseline && <div className="studio-comparison">
        <div className="studio-comparison__heading"><strong>{ui("المرجع")}</strong>{ui(inputPoint(baseline.inputs))}<span>{ui("نتيجة ناجحة محفوظة")}</span></div>
        {result && <>
          <div className="studio-comparison__heading"><strong>{ui(busy || error ? 'آخر نتيجة ناجحة' : 'الحالي · آخر نتيجة ناجحة')}</strong>{ui(resultInputs && inputPoint(resultInputs))}{busy && <span>{ui("جارٍ الحساب…")}</span>}</div>
          <div className="studio-comparison__columns" aria-hidden="true"><span>{ui("القيمة")}</span><span>{ui("المرجع")}</span><span>{ui("الحالي")}</span><span>{ui("الفرق")}</span></div><div className="studio-comparison__rows">{comparison.map(row => <div className="studio-comparison__row" key={row.key}>
            <span>{ui(row.key === 'torque_nm' ? 'العزم' : row.key === 'egt_c' ? 'حرارة العادم' : row.key === 'mdot_fuel_gps' ? 'تدفق الوقود' : 'تدفق الهواء')} <small dir="ltr">{ui(row.unit)}</small></span>
            <span dir="ltr">{ui(format(row.baseline))}</span>
            <span dir="ltr">{ui(format(row.current))}</span>
            <strong className="studio-comparison__delta" dir="ltr">{ui(signedDelta(row.delta))}</strong>
          </div>)}</div>
          <p className="studio-comparison__note">{ui("فرق عددي؛ الزيادة ليست أفضل دائمًا.")}</p>
        </>}
      </div>}
    </section>

    {warnings.length > 0 && <details className="studio-operating__warnings"><summary>{ui("تنبيهات نقطة التشغيل (")}{ui(warnings.length)})</summary><ul>{warnings.map((warning, i) => <li key={`${i}-${warning}`} title={ui(warning)}>{ui(humanWarning(warning))}</li>)}</ul></details>}
    <p className="studio-operating__note">{ui("هذه مدخلات مستقلة للنموذج؛ لا تمثل بالضرورة حالة ممكنة للمركبة على الطريق. لا تُستنتج منها حرارة الزيت أو الكتلة أو التوربين.")}</p>
  </section>;
}
