export const finite = value => typeof value === 'number' && Number.isFinite(value) ? value : null;
export function selectedPair(index, seed) {
 const pair = index?.ablation?.pairs?.find(p => p.seed === seed);
 if (!pair) return null;
 const sighted = index.policies?.[`sighted_seed${seed}`], blind = index.policies?.[`blind_seed${seed}`];
 return {pair, sighted, blind, delta: finite(pair.sighted) !== null && finite(pair.blinded) !== null ? pair.sighted-pair.blinded : null};
}
export function includesZero(ci) { return Array.isArray(ci) && ci.length === 2 && ci.every(v=>finite(v)!==null) && ci[0]<=0 && ci[1]>=0; }
export function readingProvenance(concept, reading, frame, pressure, displayedValue) {
 const value = finite(displayedValue !== undefined ? displayedValue : (pressure ? pressure.value : reading?.value));
 const live = value !== null;
 const recorded = !reading && !pressure && concept.source.file.startsWith('results/') && concept.evidence === 'STATISTIC';
 const assumption = !reading && !pressure && concept.evidence === 'ASSUMED';
 const origin = live ? (pressure ? 'derived' : 'simulated') : recorded ? 'recorded-statistic' : assumption ? 'assumption' : 'unavailable';
 const phase=reading?.phase;
 const time = !live ? null : pressure ? finite(pressure.inputS) : reading && finite(frame?.time_s)!==null ? phase==='interval' ? [finite(reading.inputS),finite(reading.endS)] : finite(phase==='end'?reading.endS:reading.inputS) : finite(frame?.time_s);
 return {value, available:live, origin, time, phase:live ? phase || (pressure?'input':'end') : 'unavailable', source:pressure?.source || `${concept.source.file}:${concept.source.line}`, quantity:concept.source.variable || concept.id, unit:reading?.unit || (['t_turb','t_oil','t_block'].includes(concept.id)?'°C':concept.unit)};
}
export const loadComparisonInputs = Object.freeze({measured:'load_meas', modeled:'load_model', formula:'100 * eta_v * (1 - f_res) * map_kpa / 100', scope:'26 points; 30–75 kPa', fitted:true});
