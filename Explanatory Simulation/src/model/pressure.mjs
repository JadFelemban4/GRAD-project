const finite = value => typeof value === 'number' && Number.isFinite(value) ? value : null;
/** obs_in is the decision input, not the observation returned at interval end. */
export function pressureReading(frame, sessionId) {
  const normalized = sessionId ? finite(frame?.obs_in?.[10]) : null;
  return { value: normalized === null ? null : normalized * 8 + 101.3, normalized, inputS: sessionId ? finite(frame?.input_time_s) : null, source: 'engine_env.py:800 · obs_in[10]' };
}
export function pressurePoints(frame, sessionId) {
  const ambient = pressureReading(frame, sessionId);
  const map = sessionId ? finite(frame?.map_kpa) : null;
  return [
    {id:'atmosphere',value:ambient.value,gaugeKpa:ambient.value === null ? null : 0,timeS:ambient.inputS},
    {id:'compressor',value:null,gaugeKpa:null,timeS:null},
    {id:'pre-throttle',value:null,gaugeKpa:null,timeS:null},
    {id:'manifold',value:map,gaugeKpa:map === null || ambient.value === null ? null : Math.round((map-ambient.value)*1e9)/1e9,timeS:sessionId ? finite(frame?.time_s) : null},
  ];
}
