import { buildProjectStory, PHYSICAL_CONTROLS } from './project-story.mjs';
const finite=v=>typeof v==='number'&&Number.isFinite(v)?v:null;
const vector=v=>Array.isArray(v)&&v.length===5&&v.every(x=>finite(x)!==null)?v:null;
export function commandChains(frame) {
  const available=buildProjectStory(frame).timeline.hasAppliedAction;
  const requested=vector(frame?.requested);
  const baseline=['spark','lam','map_kpa','fan',null];
  const finals=[frame?.spark,frame?.lam,frame?.map_kpa,frame?.command?.[3],frame?.command?.[4]];
  return PHYSICAL_CONTROLS.map((c,i)=>({...c,baseline:available&&baseline[i]?finite(frame?.baseline?.[baseline[i]]):null,requested:available?finite(requested?.[i]):null,applied:available?finite(frame?.command?.[i]):null,final:available?finite(finals[i]):null,finalUnit:i===2?'kPa abs':c.unit,dt:available?finite(frame?.dt):null}));
}
export const referenceDraft=()=>[0,0,0,1,1];
export const editorDisabled=(policy,comparison,busy)=>policy!=='manual'||!!comparison||!!busy;
export function editDraft(draft,index,value,action){return finite(value)!==null&&value>=action.lo&&value<=action.hi?draft.map((v,i)=>i===index?value:v):draft;}
export const stepControls=(policy,comparison,draft)=>policy==='manual'&&!comparison?{trims:[...draft]}:undefined;

export function commandReadings(chain, sessionId) {
  const finals = { spark_trim: 'spark', lambda_trim: 'lam', boost_trim: 'map' };
  const rows = [
    ['baseline', 'مرجع ECU / حلقة المرجع', 'baseline'],
    ['requested', 'الطلب الفيزيائي', 'requested'],
    ['applied', 'بعد حد التغيير', 'applied'],
    ['final', 'القيمة النهائية من المصدر', 'interval'],
  ];
  return rows.map(([key, label, phase]) => ({
    key, label, phase, sessionId,
    conceptId: key === 'baseline'
      ? (chain.id === 'boost_trim' ? 'map_reference' : 'baseline_ecu')
      : key === 'final' ? (finals[chain.id] || chain.id) : chain.id,
    field: 'chains.' + chain.id + '.' + key,
    unit: key === 'final' ? chain.finalUnit
      : key === 'baseline' && chain.id === 'boost_trim' ? 'kPa abs' : chain.unit,
    digits: chain.digits,
  }));
}

export function editorPresentation(activePolicy, comparison, busy) {
  return {
    showEditor: activePolicy === 'manual',
    disabled: editorDisabled(activePolicy, comparison, busy),
    message: activePolicy === 'manual' ? ''
      : 'السياسة الحالية تحدد الأوامر. المسودة اليدوية محفوظة وغير مستخدمة أثناء التشغيل الآلي.',
  };
}
