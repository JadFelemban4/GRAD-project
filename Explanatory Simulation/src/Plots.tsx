import { useUI } from './useUI';
import type { Frame, Road } from './types';
import { format } from './types';

const signals: { key: string; label: string; unit: string }[] = [
  { key: 't_turb', label: 'حرارة التوربين', unit: '°C' },
  { key: 'egt_c', label: 'حرارة العادم', unit: '°C' },
  { key: 'torque', label: 'العزم المسلّم', unit: 'Nm' },
  { key: 't_oil', label: 'حرارة الزيت', unit: '°C' },
  { key: 't_block', label: 'حرارة الكتلة', unit: '°C' },
  { key: 'mdot_fuel', label: 'تدفق الوقود', unit: 'g/s' },
  { key: 'damage_rate', label: 'معدل الضرر', unit: 'units/s' },
  { key: 'rpm', label: 'سرعة المحرك', unit: 'RPM' },
  { key: 'map_kpa', label: 'ضغط المانيفولد', unit: 'kPa abs' },
  { key: 'spark', label: 'توقيت الشرارة', unit: '°BTDC' },
  { key: 'lam', label: 'لامدا', unit: 'ratio' },
  { key: 'grade_pct', label: 'ميل الطريق', unit: '%' },
];

function signalValue(frame: Frame, key: string) {
  const value = frame[key];
  if (typeof value !== 'number' || !Number.isFinite(value)) return undefined;
  return key === 't_turb' || key === 't_oil' || key === 't_block' ? value - 273.15 : value;
}

function pathFor(frames: Frame[], key: string, width: number, height: number) {
  const values = frames.map(f => signalValue(f, key)).filter((v): v is number => v !== undefined);
  if (values.length < 2) return '';
  let lo = Math.min(...values), hi = Math.max(...values);
  if (hi - lo < 1e-9) { lo -= 1; hi += 1; }
  let started = false;
  return frames.map((f, i) => {
    const v = signalValue(f, key);
    if (v === undefined) return '';
    const x = i / (frames.length - 1) * width;
    const y = height - (v - lo) / (hi - lo) * height;
    const command = started ? 'L' : 'M';
    started = true;
    return `${command}${x.toFixed(2)},${y.toFixed(2)}`;
  }).filter(Boolean).join(' ');
}

export function Plot({ frames, compare = [], cursor = 0, onCursor = () => {} }: { frames: Frame[]; compare?: Frame[]; cursor?: number; onCursor?: (i: number) => void }) {
  const { format, ui, uiTemplate, direction } = useUI();

  if (!frames.length) return <section className="plot-panel" dir={direction}><span className="small-label">{ui("استجابة النظام")}</span><p className="empty">{ui("ستظهر المنحنيات بعد تشغيل المحاكاة.")}</p></section>;
  const current = frames[Math.min(cursor, frames.length - 1)];
  const maxTime = frames[frames.length - 1]?.time_s || 0;
  return <section className="plot-panel" aria-label={ui("استجابة النظام عبر الزمن")} dir={direction}>
    <div className="section-head"><div><span className="small-label">{ui("راقب الاستجابة")}</span><h3>{ui("كل نقطة تمثل خطوة من النموذج")}</h3></div><span className="subtle">{ui(format(current?.time_s, 0))} s / {ui(format(maxTime, 0))} s</span></div>
    <div className="plot-grid">{signals.map(({ key, label, unit }) => {
      const value = signalValue(current, key);
      return <div className="plot-card" key={key}><div className="plot-title"><span>{ui(label)}</span><strong dir="ltr"><bdi>{ui(format(value))}</bdi> <small>{ui(unit)}</small></strong></div><svg viewBox="0 0 600 72" role="img" aria-label={ui(uiTemplate("{0} عبر الزمن", "{0} over time", label))} preserveAspectRatio="none"><path d={pathFor(frames, key, 600, 64)} fill="none" stroke="#127d87" strokeWidth="2"/>{compare.length > 1 && <path d={pathFor(compare, key, 600, 64)} fill="none" stroke="#e29b45" strokeWidth="2" strokeDasharray="5 4"/>}<line x1={frames.length > 1 ? cursor / (frames.length - 1) * 600 : 0} x2={frames.length > 1 ? cursor / (frames.length - 1) * 600 : 0} y1="0" y2="68" stroke="#29464c" strokeDasharray="2 3"/></svg></div>;
    })}</div>
    <label className="plot-timeline"><span>{ui("حرّك المؤشر الزمني لاستعراض الخطوات")}</span><input aria-label={ui("المؤشر الزمني للمحاكاة")} type="range" min={0} max={frames.length - 1} value={Math.min(cursor, frames.length - 1)} onChange={e => onCursor(+e.target.value)}/><span dir="ltr">0 s — {ui(format(maxTime, 0))} s</span></label>
    <p className="subtle">{ui("الخط المتصل: السياسة المعروضة · المتقطع: السياسة المقارنة")}</p>
  </section>;
}

export function PreviewRoad({ road, frame, preview }: { road?: Road; frame?: Frame | null; preview: boolean }) {
  const { format, ui, direction } = useUI();

  if (!road?.time_s?.length) return <section className="preview-panel" dir={direction}><span className="small-label">{ui("الطريق الذي يراه الوكيل")}</span><p className="empty">{ui("لا تتوفر بيانات الطريق.")}</p></section>;
  const now = frame?.input_time_s ?? frame?.time_s ?? 0;
  const start = road.time_s[0] || 0, end = road.time_s[road.time_s.length - 1] || 0;
  const gradeAt = (t: number) => {
    let i = 0;
    while (i + 1 < road.time_s.length && road.time_s[i + 1] < t) i++;
    return road.grade_pct[Math.min(i, road.grade_pct.length - 1)] || 0;
  };
  const W = 600, H = 130;
  const lo = Math.min(...road.grade_pct, -1), hi = Math.max(...road.grade_pct, 1);
  const pts = road.time_s.map((t, i) => `${((t - start) / Math.max(1, end - start) * W).toFixed(1)},${(H - (road.grade_pct[i] - lo) / (hi - lo) * H).toFixed(1)}`).join(' ');
  const xNow = Math.max(0, Math.min(W, (now - start) / Math.max(1, end - start) * W));
  const future = frame?.preview_pct || [];
  const previewHorizons = [2, 5, 15, 30];
  return <section className="preview-panel" dir={direction}><div className="section-head"><div><span className="small-label">{ui("الطريق الذي يراه الوكيل")}</span><h3>{ui(preview ? 'المعاينة متاحة' : 'خانات المستقبل مصفّرة')}</h3></div><span className="subtle">{ui("الآن: ")}<bdi dir="ltr">{ui(format(gradeAt(now)))}%</bdi></span></div>
    <svg viewBox={`0 0 ${W} ${H}`} role="img" aria-label={ui("ميل الطريق عبر الزمن؛ المؤشر عند الزمن الحالي")} preserveAspectRatio="none"><line x1="0" x2={W} y1={H / 2} y2={H / 2} stroke="#dce4e6"/><polyline points={pts} fill="none" stroke="#127d87" strokeWidth="2"/>{preview && future.map((g, i) => { const t = now + previewHorizons[i]; const x = Math.max(0, Math.min(W, (t - start) / Math.max(1, end - start) * W)); const y = H - (g - lo) / (hi - lo) * H; return <g key={i}><circle cx={x} cy={y} r="4" fill="#e29b45"/><text x={x} y={Math.max(12, y - 8)} textAnchor="middle" fontSize="10">+{ui(previewHorizons[i])}s</text></g>; })}<line x1={xNow} x2={xNow} y1="0" y2={H} stroke="#29464c" strokeDasharray="4 3"/></svg>
    <p className="subtle">{ui("حجب المعاينة يزيل ميل الطريق المستقبلي فقط؛ ويظل الميل الحالي معلومًا لوحدة التحكم.")}</p>
  </section>;
}
