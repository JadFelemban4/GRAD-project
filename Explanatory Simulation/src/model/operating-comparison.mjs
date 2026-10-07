const inputKeys = ['rpm', 'map_kpa', 'spark', 'lam'];

export const operatingChannels = Object.freeze([
  Object.freeze({ key: 'torque_nm', unit: 'Nm' }),
  Object.freeze({ key: 'egt_c', unit: '°C' }),
  Object.freeze({ key: 'mdot_fuel_gps', unit: 'g/s' }),
  Object.freeze({ key: 'mdot_air_gps', unit: 'g/s' }),
]);

const finiteOrNull = value => typeof value === 'number' && Number.isFinite(value) ? value : null;

export function captureOperatingBaseline(successfulSnapshot) {
  if (!successfulSnapshot || typeof successfulSnapshot !== 'object') return null;
  const { inputs, result } = successfulSnapshot;
  if (!inputs || !result || typeof inputs !== 'object' || typeof result !== 'object') return null;
  if (!inputKeys.every(key => typeof inputs[key] === 'number' && Number.isFinite(inputs[key]))) return null;

  const frozenInputs = Object.freeze(Object.fromEntries(inputKeys.map(key => [key, inputs[key]])));
  const frozenResult = Object.freeze(Object.fromEntries(operatingChannels.map(({ key }) => [key, finiteOrNull(result[key])])))
  return Object.freeze({ inputs: frozenInputs, result: frozenResult });
}

export function compareOperatingResults(currentResult, baseline) {
  return operatingChannels.map(({ key, unit }) => {
    const before = finiteOrNull(baseline?.result?.[key]);
    const now = finiteOrNull(currentResult?.[key]);
    return Object.freeze({ key, baseline: before, current: now, delta: before === null || now === null ? null : now - before, unit });
  });
}
